"""Slack integration for onboarding — send welcome DMs, add to channels, post intros.

Uses real Slack API when SLACK_BOT_TOKEN is set, otherwise runs in mock mode.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger("onboard.slack")

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_API = "https://slack.com/api"
MOCK_MODE = not SLACK_TOKEN


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }


# ── Pre-configured channel map (mock mode) ──────────────────────────

MOCK_CHANNELS = {
    "#general": "C000GENERAL",
    "#random": "C000RANDOM",
    "#engineering": "C000ENGINEER",
    "#design": "C000DESIGN",
    "#standup": "C000STANDUP",
    "#hr": "C000HR",
    "#announcements": "C000ANNOUNCE",
    "#onboarding": "C000ONBOARD",
}


async def send_welcome_dm(email: str, name: str, role: str, team: str) -> dict:
    """Send a personalized welcome DM to the new hire."""
    message = f"""👋 *Welcome to ACME Corp, {name}!*

We're thrilled to have you join the *{team}* team as a *{role}*!

Here are some things to get you started:
• 📖 Read the _Company Handbook_ in Google Drive (shared with you)
• 💬 Check out the team channels you've been added to
• 🗓️ Your onboarding buddy will reach out today
• ☕ Grab a virtual coffee with your manager this week

If you need anything at all, just ask me — I'm your friendly Onboarding Bot! 🤖

_Have an amazing first day!_ 🎉"""

    if MOCK_MODE:
        logger.info(f"[MOCK] Sent welcome DM to {name} ({email})")
        return {
            "success": True,
            "mock": True,
            "message": f"Welcome DM sent to {name}",
            "channel": "D_MOCK_DM",
        }

    # Look up user by email
    async with httpx.AsyncClient() as client:
        lookup = await client.get(
            f"{SLACK_API}/users.lookupByEmail",
            headers=_headers(),
            params={"email": email},
        )
        lookup_data = lookup.json()
        if not lookup_data.get("ok"):
            return {"success": False, "error": lookup_data.get("error", "User not found")}

        user_id = lookup_data["user"]["id"]

        # Open DM channel
        conv = await client.post(
            f"{SLACK_API}/conversations.open",
            headers=_headers(),
            json={"users": user_id},
        )
        conv_data = conv.json()
        channel_id = conv_data["channel"]["id"]

        # Send message
        msg = await client.post(
            f"{SLACK_API}/chat.postMessage",
            headers=_headers(),
            json={"channel": channel_id, "text": message, "mrkdwn": True},
        )
        msg_data = msg.json()
        return {"success": msg_data.get("ok", False), "channel": channel_id}


async def add_to_channels(email: str, channels: list[str]) -> list[dict]:
    """Add a user to the specified Slack channels."""
    results = []

    for channel_name in channels:
        if MOCK_MODE:
            channel_id = MOCK_CHANNELS.get(channel_name, f"C_MOCK_{channel_name}")
            logger.info(f"[MOCK] Added {email} to {channel_name}")
            results.append({
                "channel": channel_name,
                "success": True,
                "mock": True,
                "channel_id": channel_id,
            })
            continue

        async with httpx.AsyncClient() as client:
            # Look up user
            lookup = await client.get(
                f"{SLACK_API}/users.lookupByEmail",
                headers=_headers(),
                params={"email": email},
            )
            user_id = lookup.json().get("user", {}).get("id")
            if not user_id:
                results.append({"channel": channel_name, "success": False, "error": "User not found"})
                continue

            # Invite to channel
            resp = await client.post(
                f"{SLACK_API}/conversations.invite",
                headers=_headers(),
                json={"channel": channel_name, "users": user_id},
            )
            data = resp.json()
            results.append({
                "channel": channel_name,
                "success": data.get("ok", False),
                "error": data.get("error"),
            })

    return results


async def post_intro(
    channel: str, name: str, role: str, team: str, fun_fact: Optional[str] = None
) -> dict:
    """Post an introduction message for the new hire in a channel."""
    fun_line = f"\n🎯 *Fun fact:* {fun_fact}" if fun_fact else ""
    message = f"""🎉 *Everyone, please welcome {name}!*

{name} is joining the *{team}* team as a *{role}*.{fun_line}

Drop a 👋 to say hello!"""

    if MOCK_MODE:
        logger.info(f"[MOCK] Posted intro for {name} in {channel}")
        return {
            "success": True,
            "mock": True,
            "message": f"Intro posted in {channel}",
        }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SLACK_API}/chat.postMessage",
            headers=_headers(),
            json={"channel": channel, "text": message, "mrkdwn": True},
        )
        data = resp.json()
        return {"success": data.get("ok", False), "error": data.get("error")}
