from core.log import get_logger
from core.config import settings
from prompts.messages_prompts import ButtonResponses
from services import orchestrator

logger = get_logger("UIManager")

class GoalMineUI:
    """
    Handles the construction and sending of Interactive Messages (Menus, Lists, Buttons).
    Separates the 'View' logic from the 'Controller' logic in GoalMineHandler.
    """

    def __init__(self, wa_client, db_client):
        self.wa = wa_client
        self.db = db_client

    def _send_interactive_state(self, to_number, interactive_obj):
        """Helper to send and record the UI state."""
        self.db.save_button_state(to_number, interactive_obj)
        self.wa.send_interactive_message(to_number, interactive_obj)

    async def send_main_menu(self, to_number, is_fallback=False):
        """Sends the Main Menu interactive message."""
        content = ButtonResponses.MAIN_MENU

        body_text = content["body"]
        if is_fallback:
            body_text = ButtonResponses.FALLBACK_MAIN_MENU_BODY + body_text

        buttons = []
        menu_config = settings.get(
            "BUTTON_FLOW_APP_CONFIG.menus.main", ["Show_Schedule", "Show_Help"]
        )

        for btn_id in menu_config:
            # Map ID to Title
            title = "View Schedule" if btn_id == "Show_Schedule" else "Help / Rules"
            if btn_id == "Generate_Bets" and settings.get(
                "BUTTON_FLOW_APP_CONFIG.show_generate_bets", True
            ):
                title = "🎲 Generate Bets"

            buttons.append({"type": "reply", "reply": {"id": btn_id, "title": title}})

        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": body_text},
            "footer": {"text": content["footer"]},
            "action": {"buttons": buttons[:3]},  # WhatsApp limit is 3 buttons
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_schedule_browser(self, to_number):
        """Sends the Browser with Groups and Knockouts."""
        content = ButtonResponses.SCHEDULE_BROWSER
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "footer": {"text": content["footer"]},
            "action": {
                "button": content["button"],
                "sections": [{"title": "Tournament Phases", "rows": content["rows"]}],
            },
        }
        logger.info(f"📅 Outgoing: Schedule Browser sent to {to_number}")
        self._send_interactive_state(to_number, interactive_obj)

    async def send_groups_selection(self, to_number):
        """Sends Group A-E selector."""
        content = ButtonResponses.GROUP_SELECTOR
        # Just show A-F and a row for "G-L Next ->"
        rows_1 = [
            {"id": f"Group_{g}", "title": f"Group {g}"}
            for g in ["A", "B", "C", "D", "E"]
        ]
        rows_1.append({"id": "Show_Groups_G_L", "title": "Next: Groups G-L ➡️"})

        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "action": {
                "button": content["button"],
                "sections": [
                    {"title": "Select Group", "rows": rows_1}
                ]
            }
        }
        logger.info(f"🌍 Outgoing: Group Selector (A-E) sent to {to_number}")
        self._send_interactive_state(to_number, interactive_obj)

    async def send_groups_g_l(self, to_number):
        """Sends Group G-L selector."""
        content = ButtonResponses.GROUP_SELECTOR_GL
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "action": {
                "button": content["button"],
                "sections": [
                    {
                        "title": "Groups G-L",
                        "rows": [
                            {"id": f"Group_{g}", "title": f"Group {g}"}
                            for g in ["G", "H", "I", "J", "K", "L"]
                        ],
                    },
                    {
                        "title": "Navigation",
                        "rows": [{"id": "Show_Groups_Menu", "title": "⬅️ Back to A-E"}],
                    },
                ],
            },
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_knockouts_selection(self, to_number):
        """Sends Knockout Stage selector."""
        content = ButtonResponses.KNOCKOUT_SELECTOR
        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "action": {
                "button": content["button"],
                "sections": [{"title": "Knockout Brackets", "rows": content["rows"]}],
            },
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_group_matches(self, to_number, filter_name, is_stage=False):
        """Sends matches for a specific group or stage."""
        all_matches = orchestrator.get_active_schedule()

        if is_stage:
            matches = [m for m in all_matches if m.get("stage") == filter_name]
        else:
            matches = [m for m in all_matches if m.get("group") == filter_name]

        if not matches:
            self.wa.send_message(
                to_number, ButtonResponses.NO_MATCHES.format(filter_name=filter_name)
            )
            await self.send_schedule_browser(to_number)
            return

        rounds = {}
        for idx, m in enumerate(matches):
            date_str = m["date_iso"].split("T")[0]
            if date_str not in rounds:
                rounds[date_str] = []
            rounds[date_str].append(m)

        sections = []
        for i, (date, m_list) in enumerate(sorted(rounds.items())):
            round_label = f"Matchday {i + 1} ({date})"
            rows = []
            for m in m_list:
                home = m["team_home"]
                away = m["team_away"]
                is_tbd = "TBD" in home or "TBD" in away

                if is_tbd:
                    row_id = f"LOCKED_TBD_{home}_{away}"
                    title = f"🔒 {home[:7]} vs {away[:7]}"
                    desc = "Fixture not yet determined."
                else:
                    row_id = f"Analyze {home} vs {away}"
                    title = f"{home[:9]} vs {away[:9]}"
                    desc = f"{m['date_iso'].split('T')[1][:5]} @ {m.get('venue', 'Stadium')[:30]}"

                rows.append({"id": row_id, "title": title, "description": desc})

            sections.append({"title": round_label, "rows": rows})

        interactive_obj = {
            "type": "list",
            "header": {"type": "text", "text": f"🏆 {filter_name}"},
            "body": {
                "text": ButtonResponses.MATCH_LIST_BODY.format(filter_name=filter_name)
            },
            "footer": {"text": ButtonResponses.MATCH_LIST_FOOTER},
            "action": {
                "button": ButtonResponses.MATCH_LIST_BUTTON,
                "sections": sections,
            },
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_help_menu(self, to_number):
        """Sends the Help/About info."""
        support = settings.get("GLOBAL_APP_CONFIG.app.support_contact", "@Admin")
        msg = ButtonResponses.HELP_MENU + f"\n\nFor support, contact {support}"

        nav_obj = {
            "type": "button",
            "body": {"text": msg},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": "Show_MainMenu", "title": "🔙 Main Menu"},
                    }
                ]
            },
        }
        self._send_interactive_state(to_number, nav_obj)

    async def send_bet_menu(self, to_number):
        """Sends the Quantity Selection Menu."""
        content = ButtonResponses.BET_GENERATION_MENU

        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "footer": {"text": content["footer"]},
            "action": {
                "buttons": [{"type": "reply", "reply": b} for b in content["buttons"]]
            },
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_analysis_footer(self, to_number):
        """Sends the post-analysis navigation options."""
        content = ButtonResponses.ANALYSIS_FOOTER
        buttons = []
        if settings.get("BUTTON_FLOW_APP_CONFIG.show_generate_bets", True):
            buttons.append(
                {
                    "type": "reply",
                    "reply": {"id": "Generate_Bets", "title": "🎲 Generate Bets"},
                }
            )

        buttons.append(
            {
                "type": "reply",
                "reply": {"id": "Show_Schedule", "title": "📅 More Matches"},
            }
        )

        if settings.get("BUTTON_FLOW_APP_CONFIG.show_back_button", True):
            buttons.append(
                {
                    "type": "reply",
                    "reply": {"id": "Show_MainMenu", "title": "🔙 Main Menu"},
                }
            )

        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "action": {"buttons": buttons[:3]},
        }
        self._send_interactive_state(to_number, interactive_obj)

    async def send_bet_footer(self, to_number):
        """Sends navigation options AFTER bets are generated."""
        content = ButtonResponses.BET_FOOTER
        interactive_obj = {
            "type": "button",
            "header": {"type": "text", "text": content["header"]},
            "body": {"text": content["body"]},
            "action": {
                "buttons": [{"type": "reply", "reply": b} for b in content["buttons"]]
            },
        }
        self._send_interactive_state(to_number, interactive_obj)
