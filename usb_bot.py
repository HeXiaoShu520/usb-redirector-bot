#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB Redirector Bot — HTTP API for remote USB device management.
Drives usbrdrsh.exe (CLI) so no desktop session is required.

Environment variables:
    USBRDRSH_PATH    — path to usbrdrsh.exe  (default: C:\\Program Files\\USB Redirector\\usbrdrsh.exe)
    USBRDRSH_TIMEOUT — command timeout in seconds (default: 10)
    PORT             — HTTP listen port (default: 5000)
"""

import logging
import os
import re
import subprocess

from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────
USBRDRSH = os.environ.get("USBRDRSH_PATH", r"C:\Program Files\USB Redirector\usbrdrsh.exe")
CMD_TIMEOUT = int(os.environ.get("USBRDRSH_TIMEOUT", "10"))


class USBRedirectorBot:
    """Wraps usbrdrsh.exe CLI to provide programmatic USB device control."""

    def _run_cmd(self, args: list[str]) -> str:
        """Execute a usbrdrsh.exe command and return combined stdout+stderr."""
        try:
            result = subprocess.run(
                [USBRDRSH, *args],
                capture_output=True, text=True, timeout=CMD_TIMEOUT,
                encoding="utf-8", errors="replace",
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "ERROR: command timed out"
        except FileNotFoundError:
            return f"ERROR: usbrdrsh.exe not found at {USBRDRSH}"
        except Exception as e:
            return f"ERROR: {e}"

    # ── Parsing ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_devices(output: str) -> list[dict]:
        """
        Parse `-list-devices` output into structured device dicts.

        Expected format per device:
            <id>: <device name>
              Vid: <vid>  Pid: <pid>
              Status: <status text>
        """
        devices: list[dict] = []
        current: dict | None = None

        for raw_line in output.splitlines():
            line = raw_line.strip()
            # Device header line, e.g. "4: Vector - USB Human Interface Device"
            match = re.match(r"^(\d+):\s+(.+)$", line)
            if match:
                if current:
                    devices.append(current)
                current = {
                    "id": int(match.group(1)),
                    "name": match.group(2).strip(),
                    "vid": "", "pid": "", "status": "",
                }
            elif current:
                # Vendor / Product ID line
                vid = re.search(r"Vid:\s*(\w+)", line)
                pid = re.search(r"Pid:\s*(\w+)", line)
                if vid:
                    current["vid"] = vid.group(1)
                if pid:
                    current["pid"] = pid.group(1)
                # Status line
                status = re.match(r"^Status:\s+(.+)$", line)
                if status:
                    current["status"] = status.group(1).strip()

        if current:
            devices.append(current)
        return devices

    def _find_device(self, keyword: str) -> tuple[dict | None, list[dict]]:
        """
        Find a device by name keyword (case-insensitive fuzzy match).
        Returns (last_matched_device, all_devices).
        """
        output = self._run_cmd(["-list-devices"])
        devices = self._parse_devices(output)
        matched = [d for d in devices if keyword.lower() in d["name"].lower()]
        return (matched[-1] if matched else None), devices

    # ── Device operations ────────────────────────────────────────────

    def list_devices(self, **_):
        """List all USB devices with their current status."""
        output = self._run_cmd(["-list-devices"])
        devices = self._parse_devices(output)
        if not devices:
            return {"status": "error", "message": f"No devices found. Raw: {output.strip()}"}
        return {
            "status": "success",
            "devices": [f"{d['name']} (ID:{d['id']}, Status:{d['status']})" for d in devices],
            "raw": devices,
        }

    def share_device(self, device_name: str | None = None, **_):
        """Share a USB device so remote clients can connect to it."""
        if not device_name:
            return {"status": "error", "message": "device is required"}
        device, _ = self._find_device(device_name)
        if not device:
            return {"status": "error", "message": f"Device not found: {device_name}"}

        st = device["status"]
        # Already shared or in use — no action needed
        if "shared" in st or "in use by" in st:
            return {"status": "info", "message": f"{device['name']} (ID:{device['id']}) already shared. Status: {st}"}

        out = self._run_cmd(["-share", str(device["id"])])
        if "OPERATION SUCCESSFUL" in out:
            return {"status": "success", "message": f"Shared: {device['name']} (ID:{device['id']})"}
        return {"status": "error", "message": f"Share failed: {out.strip()}"}

    def unshare_device(self, device_name: str | None = None, **_):
        """Stop sharing a USB device. Fails if a client is still connected."""
        if not device_name:
            return {"status": "error", "message": "device is required"}
        device, _ = self._find_device(device_name)
        if not device:
            return {"status": "error", "message": f"Device not found: {device_name}"}

        st = device["status"]
        # Cannot unshare while a client holds the device
        if "in use by" in st:
            return {"status": "error", "message": f"{device['name']} (ID:{device['id']}) is in use — disconnect first. Status: {st}"}
        if "shared" not in st:
            return {"status": "info", "message": f"{device['name']} (ID:{device['id']}) is not shared. Status: {st}"}

        out = self._run_cmd(["-unshare", str(device["id"])])
        if "OPERATION SUCCESSFUL" in out:
            return {"status": "success", "message": f"Unshared: {device['name']} (ID:{device['id']})"}
        return {"status": "error", "message": f"Unshare failed: {out.strip()}"}

    def connect_device(self, device_name: str | None = None, **_):
        """Make a device available for client connection (auto-shares if needed)."""
        if not device_name:
            return {"status": "error", "message": "device is required"}
        device, _ = self._find_device(device_name)
        if not device:
            return {"status": "error", "message": f"Device not found: {device_name}"}

        st = device["status"]
        if "in use by" in st:
            return {"status": "info", "message": f"{device['name']} (ID:{device['id']}) already connected. Status: {st}"}
        if "shared" in st:
            return {"status": "info", "message": f"{device['name']} (ID:{device['id']}) already shared, awaiting client. Status: {st}"}

        # Device not shared yet — share it so clients can connect
        out = self._run_cmd(["-share", str(device["id"])])
        if "OPERATION SUCCESSFUL" in out:
            return {"status": "success", "message": f"Shared: {device['name']} (ID:{device['id']}), awaiting client"}
        return {"status": "error", "message": f"Share failed: {out.strip()}"}

    def disconnect_device(self, device_name: str | None = None, **_):
        """Force-disconnect a device from its current client."""
        if not device_name:
            return {"status": "error", "message": "device is required"}
        device, _ = self._find_device(device_name)
        if not device:
            return {"status": "error", "message": f"Device not found: {device_name}"}

        st = device["status"]
        out = self._run_cmd(["-disconnect-from", str(device["id"])])
        if "OPERATION SUCCESSFUL" in out:
            return {"status": "success", "message": f"Disconnected: {device['name']} (ID:{device['id']}), was: {st}"}
        return {"status": "error", "message": f"Disconnect failed: {out.strip()}, status: {st}"}


# ── Application setup ────────────────────────────────────────────────

bot = USBRedirectorBot()

# Command name → handler mapping for dispatch
COMMANDS = {
    "list":       bot.list_devices,
    "share":      bot.share_device,
    "unshare":    bot.unshare_device,
    "connect":    bot.connect_device,
    "disconnect": bot.disconnect_device,
}


@app.route("/command", methods=["POST"])
def handle_command():
    """
    Unified command endpoint.
    Expects JSON: {"command": "<name>", "device": "<keyword>"}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    command = data.get("command", "").lower().strip()
    handler = COMMANDS.get(command)
    if not handler:
        return jsonify({
            "status": "error",
            "message": f"Unknown command: {command}. Available: {', '.join(COMMANDS)}",
        }), 400

    result = handler(device_name=data.get("device"))
    log.info("%s device=%s -> %s", command, data.get("device"), result.get("status"))
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness probe."""
    return jsonify({"status": "running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    log.info("USB Redirector Bot starting on port %d (CLI mode, no desktop required)", port)
    app.run(host="0.0.0.0", port=port)
