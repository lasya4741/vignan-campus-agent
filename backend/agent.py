"""VIGNAN Campus Intelligence Coordinator Agent.

Provides natural language understanding, multi-tool orchestration, verified factual grounding,
and Google Maps navigation integration across university data.
"""

import os
import re
from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.gemini_client import gemini_service, types
from backend.models.responses import (
    ChatResponse,
    LiveStatusDetail,
    LocationDetail,
    RouteDetail,
    RouteStep,
    SourceMetadata,
    ToolCallRecord,
)
from backend.tools import ALL_TOOLS
from backend.utils.campus_entities import (
    OUT_OF_SCOPE_REFUSAL,
    CampusIntent,
    classify_campus_intent,
    is_out_of_scope,
    resolve_campus_entity,
    strip_honorifics,
)
from backend.utils.logging import logger
from backend.utils.normalization import normalize_text

SYSTEM_INSTRUCTION = """You are VIGNAN, the official AI Campus Intelligence Agent for Vignan's Foundation for Science, Technology & Research (VFSTR / Vignan University), Vadlamudi.

Your core mission is to provide accurate, concise, grounded, and verified information to students, faculty, and visitors regarding:
1. University Faculty (names, designations, departments, rooms, phones, official profiles, verified research areas, verified teaching engagements).
2. Academic Departments & Heads of Department (HODs) across all disciplines (CSE, IT, ECE, EEE, Mechanical, Civil, Biotechnology, etc.).
3. Campus Offices (Finance & Accounts Office for tuition fees and dues, Transport Office for bus passes, Board of Examinations, Placements).
4. Campus Facilities & Canteens (MHP / Main Canteen, H Block Canteen, Xerox shops, Central Library).
5. Student Counsellors & Academic Mentors (lookup by Year and Section).
6. Campus Navigation & Directions (walking routes between blocks/landmarks and Google Maps navigation).
7. Live Status & Queue Intelligence (real-time wait times and best service recommendations).

CRITICAL GROUNDING & VERIFICATION RULES:
- Ground your answers STRICTLY in the records retrieved from your tools.
- Never invent faculty room numbers, phone numbers, email addresses, HOD names, or course assignments.
- If information is not available in the database (e.g. an HOD whose exact room is not listed), explicitly state: "Room number is not available in the verified faculty data."
- If the user asks an out-of-scope question (coding, physics lectures, general world trivia, jokes, sports scores), refuse politely with: "I'm the VIGNAN Campus Intelligence Assistant. I can help with verified information about VIGNAN University, including faculty, departments, offices, services, counsellors, and campus locations."
- For questions beginning with "Who is the HOD of [Dept]" or "Who heads [Dept]": prioritize person identity first (e.g. "**[Name]** is the current Head of the [Department] Department.").
- For "Who is [Person]": return concise identity and role without dumping their entire publication history.
- For "Where is [Person]": return verified room and block location.
- For "What does [Person] teach": return only verified teaching engagements.
- For "What does [Person] research": return only verified research interests.
- For MHP / Main Canteen questions ("Where is MHP?", "Where can I get lunch?", "Where do students eat?"): resolve to MHP / Main Canteen at Central Campus.
- For Navigation queries ("How do I get from A to B?", "Take me to Finance", "Show me the route to Xerox"): invoke get_route and provide step-by-step guidance and Google Maps link.
"""


class CoordinatorAgent:
    """Core Agent coordinating Gemini tool-calling, verified fallback routing, and response synthesis."""

    def __init__(self, model_name: Optional[str] = None):
        self.model = model_name or settings.gemini_model
        self.gemini = gemini_service

    def run(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        user: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Synchronous entry point for coordinator agent execution."""
        if not message or not message.strip():
            return ChatResponse(
                answer="Please enter a valid campus query.",
                confidence="high",
                requires_clarification=False,
            )

        if gemini_service.is_configured() and types:
            try:
                return self._run_with_gemini(message, history, user)
            except Exception as e:
                logger.error(f"Gemini API invocation failed: {e}. Falling back to deterministic tool router.")
                return self._run_fallback(message, user)
        else:
            logger.info("Gemini API not configured. Executing query via deterministic tool router.")
            return self._run_fallback(message, user)

    async def process_query(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        user: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Process incoming user query, execute required tool calls, and generate verified response."""
        return self.run(message, history, user)

    def _run_with_gemini(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        user: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Execute query using Gemini 3.7 with native tool calling."""
        client = gemini_service.client
        tool_records: List[ToolCallRecord] = []
        executed_tools: List[str] = []

        wrapped_tools = []
        for name, func in ALL_TOOLS.items():
            def make_wrapper(f, tool_name):
                def wrapper(**kwargs):
                    logger.info(f"Agent executing tool '{tool_name}' with args {kwargs}")
                    res = f(**kwargs)
                    tool_records.append(ToolCallRecord(tool_name=tool_name, arguments=kwargs, result=res))
                    if tool_name not in executed_tools:
                        executed_tools.append(tool_name)
                    return res
                wrapper.__name__ = f.__name__
                wrapper.__doc__ = f.__doc__
                return wrapper
            wrapped_tools.append(make_wrapper(func, name))

        sys_inst = SYSTEM_INSTRUCTION
        if user:
            sys_inst += f"\n\nAUTHENTICATED USER CONTEXT:\n- Name: {user.get('name', 'Student')}\n- Email: {user.get('email', '')}\n- Department: {user.get('department', 'CSE')}\n- Year: {user.get('year', 'Not specified')}\n- Section: {user.get('section', 'Not specified')}"

        chat_contents = []
        if history:
            for turn in history[-6:]:
                role = "user" if turn.get("role") == "user" else "model"
                chat_contents.append(types.Content(role=role, parts=[types.Part.from_text(turn.get("content", ""))]))

        chat_contents.append(types.Content(role="user", parts=[types.Part.from_text(message)]))

        config = types.GenerateContentConfig(
            system_instruction=sys_inst,
            tools=wrapped_tools,
            temperature=0.1,
        )

        response = client.models.generate_content(
            model=self.model,
            contents=chat_contents,
            config=config,
        )

        answer_text = response.text or "I processed your request using the verified VIGNAN database."
        return self._build_chat_response(answer_text, executed_tools, tool_records)

    def _run_fallback(
        self,
        message: str,
        user: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Deterministic offline intent classification and tool execution fallback."""
        tool_records: List[ToolCallRecord] = []
        executed_tools: List[str] = []
        norm_msg = normalize_text(message)

        def execute_tool(tool_name: str, **kwargs):
            func = ALL_TOOLS.get(tool_name)
            if func:
                logger.info(f"Fallback executing tool '{tool_name}' with args {kwargs}")
                res = func(**kwargs)
                tool_records.append(ToolCallRecord(tool_name=tool_name, arguments=kwargs, result=res))
                if tool_name not in executed_tools:
                    executed_tools.append(tool_name)
                return res
            return None

        intent, details = classify_campus_intent(message, user_context=user)

        # 1. Out of Scope
        if intent == CampusIntent.OUT_OF_SCOPE_REQUEST:
            return ChatResponse(
                answer=details.get("refusal", OUT_OF_SCOPE_REFUSAL),
                confidence="high",
                requires_clarification=False,
                executed_tools=[],
                tool_calls=[],
            )

        # 2. Clarification Required
        if intent == CampusIntent.CLARIFICATION_REQUIRED:
            return ChatResponse(
                answer=details.get("question", "Could you please specify which campus department, office, or facility you mean?"),
                confidence="high",
                requires_clarification=True,
                executed_tools=[],
                tool_calls=[],
            )

        # 3. Counsellor Lookup
        if intent == CampusIntent.COUNSELLOR_LOOKUP:
            year = details.get("year")
            section = details.get("section")
            reg_num = details.get("registration_number")

            if year and section:
                res = execute_tool("search_counsellor", year=year, section=section)
                if res and res.get("matches"):
                    matches = res["matches"]
                    ans = f"**Assigned Counsellors for Year {year}, Section {section}** ({len(matches)} faculty):\n"
                    for c in matches:
                        room_str = f"Room {c.get('room')}" if c.get('room') else "Room N/A"
                        phone_str = f", Phone: {c.get('phone')}" if c.get('phone') else ""
                        range_str = f"\n  - *Roll Range*: {c['registration_range']}" if c.get("registration_range") else ""
                        ans += f"- **{c['counsellor_name']}** ({room_str}{phone_str}){range_str}\n"
                    return self._build_chat_response(ans, executed_tools, tool_records)
                else:
                    ans = f"No verified counsellor records found for Year {year}, Section {section}."
                    return self._build_chat_response(ans, executed_tools, tool_records)

            if reg_num:
                res = execute_tool("search_counsellor", registration_number=reg_num, year=year)
                if res and res.get("matches"):
                    matches = res["matches"]
                    m = matches[0]
                    room_str = f"Room {m.get('room')}" if m.get('room') else "Room N/A"
                    phone_str = f", Phone: {m.get('phone')}" if m.get('phone') else ""
                    range_str = f" (Roll Range: {m['registration_range']})" if m.get("registration_range") else ""
                    ans = f"For registration number **{reg_num}** (Year {m.get('year')}, Section {m.get('section')}):\n- **Counsellor**: **{m['counsellor_name']}** ({room_str}{phone_str}){range_str}"
                    return self._build_chat_response(ans, executed_tools, tool_records)

            if year and not section:
                return ChatResponse(
                    answer=f"Sure! Which section are you in for Year {year}? (e.g. Section 1, Section 8)",
                    confidence="high",
                    requires_clarification=True,
                    tool_used=[],
                    tool_calls=[],
                    sources=[],
                )

            return ChatResponse(
                answer="To look up your counsellor, please provide your **Year and Section** (e.g., *Year 2, Section 8* or *Year 3, Section 8*).",
                confidence="high",
                requires_clarification=True,
                tool_used=[],
                tool_calls=[],
                sources=[],
            )

        # 4. Best Service / Shortest Queue Recommendation
        if intent == CampusIntent.BEST_SERVICE_REQUEST:
            cat = details.get("category", "xerox")
            res = execute_tool("find_best_service", category=cat)
            rec = res.get("recommended_service") or res.get("recommendation") if res else None
            if rec:
                ls = rec.get("live_status") or {}
                rationale = res.get("decision_reason") or res.get("rationale") or "Optimal facility based on live status."
                ans = f"**Recommended {cat.title()} Facility**: **{rec['name']}**\n- **Location**: {rec.get('location') or 'Campus'}\n- **Current Queue**: {ls.get('queue_length', 0)} students\n- **Est. Wait Time**: {ls.get('estimated_wait_minutes', 0)} minutes\n- **Status**: {ls.get('status', 'Active')}\n- **Why**: {rationale}"
                return self._build_chat_response(ans, executed_tools, tool_records)
            else:
                ans = f"No live queue data currently recorded for {cat} facilities. Current availability cannot be verified."
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 5. Live Queue Status
        if intent == CampusIntent.LIVE_STATUS_REQUEST:
            s_res = execute_tool("search_service", query=message)
            if s_res and s_res.get("matches"):
                serv = s_res["matches"][0]
                live_res = execute_tool("get_live_status", service_id=serv["id"])
                if live_res and live_res.get("current_status"):
                    cs = live_res["current_status"]
                    ans = f"**Live Status for {serv['name']}**:\n- **Status**: {cs.get('status', 'Active')}\n- **Queue**: {cs.get('queue_length', 0)} students\n- **Est. Wait Time**: {cs.get('estimated_wait_minutes', 0)} minutes"
                    return self._build_chat_response(ans, executed_tools, tool_records)
            ans = "Current availability and queue length cannot be verified for that facility at this moment."
            return self._build_chat_response(ans, executed_tools, tool_records)

        # 6. Navigation / Directions
        if intent == CampusIntent.NAVIGATION_REQUEST:
            clean_msg = re.sub(r"[?!.,]+$", "", message).strip()
            route_match = re.search(r"from\s+([a-zA-Z0-9\s]+?)\s+(?:to|destination)\s+([a-zA-Z0-9\s]+?)(?:\s+directions|\s+route)?$", clean_msg, re.IGNORECASE)
            if not route_match:
                route_match = re.search(r"(?:how do i go from|how to go from|navigate from|route from|how do i get from)\s+([a-zA-Z0-9\s]+?)\s+to\s+([a-zA-Z0-9\s]+?)$", clean_msg, re.IGNORECASE)

            if route_match:
                start_loc = route_match.group(1).strip()
                dest_loc = route_match.group(2).strip()
            else:
                start_loc = "Main Gate"
                dest_loc = re.sub(r"(?i)\b(how do i get to|how to reach|take me to|directions to|route to|way to|how can i reach|show me the route to|show me the route|how do i get)\b", "", clean_msg).strip()
                if not dest_loc or dest_loc.lower() in ["the", "a", "an"]:
                    dest_loc = clean_msg

            start_loc = re.sub(r"[.?!]+$", "", start_loc).strip()
            dest_loc = re.sub(r"[.?!]+$", "", dest_loc).strip()

            res = execute_tool("get_route", start_location=start_loc, destination=dest_loc, travel_mode="walking")
            if res and res.get("found"):
                steps_text = "\n".join([f"{s['step']}. {s['instruction']}" for s in res.get("steps", [])])
                guidance_text = f"\n\n*Indoor Guidance*: {res['indoor_guidance']}" if res.get("indoor_guidance") else ""
                maps_link = f"\n\n[Open in Google Maps]({res['google_maps_url']})"
                ans = (
                    f"**Route from {res['origin']} to {res['destination']}** (Walking, ~{res.get('estimated_minutes', 3)} mins):\n"
                    f"{steps_text}"
                    f"{guidance_text}"
                    f"{maps_link}"
                )
            else:
                ans = res.get("message", f"A verified step-by-step route between '{start_loc}' and '{dest_loc}' is currently unavailable in the campus database.")
            return self._build_chat_response(ans, executed_tools, tool_records)

        # 7. Department & HOD Lookup (High Priority)
        if intent == CampusIntent.DEPARTMENT_LOOKUP:
            res = execute_tool("search_department", query=message)
            if res and res.get("matches"):
                matches = res["matches"]
                d = matches[0]
                hod = d.get("hod") or {}
                is_hod_query = any(w in norm_msg for w in ["hod", "head", "chairperson", "leader", "who leads", "who heads", "head of department", "head of the department", "who is the head", "who is the hod"])
                is_where_hod = is_hod_query and any(w in norm_msg for w in ["where", "room", "cabin", "meet", "location"])

                if is_where_hod and hod and hod.get("name"):
                    if hod.get("room"):
                        ans = f"**{hod['name']}** ({hod.get('designation') or 'HOD'}, {d['name']}) is located in **Room {hod['room']}** ({d.get('block') or 'Campus Block'})."
                    else:
                        ans = f"**{hod['name']}** ({hod.get('designation') or 'HOD'}, {d['name']}) is located in **{d.get('block') or 'Campus Block'}**. Their room number is not available in the verified faculty data."
                    if hod.get("email"):
                        ans += f"\n- **Email**: {hod['email']}"
                    return self._build_chat_response(ans, executed_tools, tool_records)

                if is_hod_query and hod and hod.get("name"):
                    ans = f"**{hod['name']}** is the current Head of the {d['name']} Department."
                    if hod.get("designation"):
                        ans += f"\n- **Designation**: {hod['designation']}"
                    if hod.get("email"):
                        ans += f"\n- **Email**: {hod['email']}"
                    if hod.get("room"):
                        ans += f"\n- **Room**: {hod['room']} ({d.get('block') or 'Campus Block'})"
                    elif d.get("block"):
                        ans += f"\n- **Location**: {d.get('block')} (Room number is not available in the verified faculty data)"
                    if hod.get("profile_url"):
                        ans += f"\n- **Official Profile**: {hod['profile_url']}"
                    return self._build_chat_response(ans, executed_tools, tool_records)

                is_block_query = any(re.search(rf"\b{re.escape(b)}\b", norm_msg) for b in ["u block", "n block", "h block", "a block", "textile block"])
                if (any(w in norm_msg for w in ["which departments", "departments in", "list departments"]) or len(matches) > 1) and is_block_query and not any(w in norm_msg for w in ["which block has", "what building is", "where is"]):
                    block_name = "U Block" if re.search(r"\bu block\b", norm_msg) else ("N Block" if re.search(r"\bn block\b", norm_msg) else ("H Block" if re.search(r"\bh block\b", norm_msg) else "Campus"))
                    ans = f"**Departments in {block_name}** ({len(matches)} departments):\n"
                    for dm in matches:
                        ans += f"- **{dm['name']} ({dm.get('short_name') or ''})**: {dm.get('floor_information') or 'Floor info available'}\n"
                else:
                    ans = f"**{d['name']} ({d.get('short_name') or ''})**\n- **Building Block**: {d.get('block') or 'Campus'}\n- **Floor**: {d.get('floor_information') or 'N/A'}\n- **Description**: {d.get('description') or 'N/A'}"
                    if hod and hod.get("name"):
                        ans += f"\n- **Head of Department (HOD)**: {hod.get('name')} ({hod.get('designation') or 'HOD'}, Email: {hod.get('email') or 'N/A'}, Room: {hod.get('room') or 'Not Available'})"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 8. Responsibilities / Roles / Student Affairs / Placements
        if intent == CampusIntent.RESPONSIBILITY_LOOKUP:
            res = execute_tool("search_responsibility", query=message)
            if res and res.get("matches"):
                m = res["matches"][0]
                ans = f"**{m['role_name']}**: **{m['person_name']}**\n- **Responsibilities**: {m.get('responsibilities') or 'N/A'}\n- **Room**: {m.get('room') or 'N/A'} ({m.get('block') or 'Campus'})\n- **Contact**: {m.get('email') or m.get('phone') or 'N/A'}"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 9. Services (MHP, Canteen, Food, Lunch, Xerox, Photocopy, Printing, Transport, Bus Pass)
        if intent == CampusIntent.SERVICE_LOOKUP:
            resolved_entity = resolve_campus_entity(message)
            cat = resolved_entity.get("category") if resolved_entity else None
            res = execute_tool("search_service", query=message, category=cat)
            if not res or not res.get("matches"):
                if resolved_entity and resolved_entity.get("canonical_name"):
                    res = execute_tool("search_service", query=resolved_entity["canonical_name"], category=cat)

            if res and res.get("matches"):
                matches = res["matches"]
                if len(matches) == 1:
                    m = matches[0]
                    loc = m.get("location") or {}
                    loc_desc = loc.get("name") or loc.get("block") or m.get("description") or "Campus"
                    ans = f"**{m['name']}**\n- **Location**: {loc_desc} (Block: {loc.get('block') or 'Central Campus'}, Floor: {loc.get('floor') or 'Ground'})\n- **Services**: {', '.join(m.get('services_offered', []))}\n- **Description**: {m.get('description') or 'Campus Facility'}"
                else:
                    ans = f"Found {len(matches)} verified campus facility/facilities:\n"
                    for m in matches[:3]:
                        loc = m.get("location") or {}
                        loc_desc = loc.get("name") or loc.get("block") or "Campus"
                        ans += f"- **{m['name']}**: {loc_desc} (Services: {', '.join(m.get('services_offered', []))})\n"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 10. Offices (Finance, Accounts, Fees)
        if intent == CampusIntent.OFFICE_LOOKUP:
            res = execute_tool("search_office", query=message)
            if res and res.get("matches"):
                o = res["matches"][0]
                ans = f"**{o['name']}**\n- **Location**: {o.get('block') or 'Campus'}, {o.get('floor') or 'Floor Info'}\n- **Room**: {o.get('room') or 'N/A'}\n- **Purpose**: {o.get('purpose') or o.get('description') or 'N/A'}\n- **Contact**: {o.get('phone') or o.get('email') or 'N/A'}"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 11. Faculty Search / Research / Teaching / Identity
        if intent == CampusIntent.FACULTY_LOOKUP:
            res = execute_tool("search_faculty", query=message)
            if res and res.get("matches"):
                f = res["matches"][0]
                is_who_query = any(w in norm_msg for w in ["who is", "who's", "tell me about", "who was", "profile of", "about dr", "about mr", "about prof"])
                is_research_query = any(w in norm_msg for w in ["research", "researches", "areas of research", "research interest", "specialization", "papers", "what does he research", "what does she research"])
                is_teaching_query = any(w in norm_msg for w in ["teach", "teaches", "teaching", "course", "courses", "subject", "subjects", "what does he teach", "what does she teach"])
                is_where_query = any(w in norm_msg for w in ["where", "room", "cabin", "floor", "meet", "find", "located"])

                if is_research_query:
                    interests = f.get("research_interests") or []
                    if interests:
                        items_str = "\n".join([f"- {r}" for r in interests])
                        ans = f"**{f['full_name']}**'s verified research areas include:\n{items_str}"
                    else:
                        ans = f"Research interest information for **{f['full_name']}** is not explicitly listed in the verified faculty database."
                    return self._build_chat_response(ans, executed_tools, tool_records)

                if is_teaching_query:
                    engagements = f.get("teaching_engagements") or []
                    if engagements:
                        items_str = "\n".join([f"- {t}" for t in engagements])
                        ans = f"**{f['full_name']}**'s verified teaching engagements and courses include:\n{items_str}"
                    else:
                        ans = f"Explicit teaching course assignments for **{f['full_name']}** are not recorded in the verified faculty database."
                    return self._build_chat_response(ans, executed_tools, tool_records)

                if is_where_query:
                    if f.get("room"):
                        ans = f"**{f['full_name']}** ({f.get('designation') or 'Faculty'}) is located in **Room {f['room']}** ({f.get('block') or 'Campus'})."
                    else:
                        ans = f"**{f['full_name']}** ({f.get('designation') or 'Faculty'}) is in the {f.get('department') or 'Campus'} department ({f.get('block') or 'Campus'}). Their room number is not available in the verified faculty data."
                    if f.get("email"):
                        ans += f"\n- **Email**: {f['email']}"
                    if f.get("phone"):
                        ans += f"\n- **Phone**: {f['phone']}"
                    return self._build_chat_response(ans, executed_tools, tool_records)

                if is_who_query:
                    admin_pos = f.get("academic_profile", {}).get("admin_positions") if f.get("academic_profile") else None
                    pos_str = f" and serves as the {admin_pos[0]}" if admin_pos and isinstance(admin_pos, list) and admin_pos else ""
                    ans = f"**{f['full_name']}** is an {f.get('designation') or 'Faculty Member'} in the {f.get('department') or 'Campus'} Department{pos_str}."
                    if f.get("room"):
                        ans += f"\n- **Room**: {f['room']} ({f.get('block') or 'Campus'})"
                    elif f.get("block"):
                        ans += f"\n- **Location**: {f.get('block')} (Room number is not available in the verified faculty data)"
                    if f.get("email"):
                        ans += f"\n- **Email**: {f['email']}"
                    if f.get("phone"):
                        ans += f"\n- **Phone**: {f['phone']}"
                    if f.get("profile_url"):
                        ans += f"\n- **Official Profile**: {f['profile_url']}"
                    return self._build_chat_response(ans, executed_tools, tool_records)

                # Standard overview
                ans = f"**{f['full_name']}** ({f.get('designation') or 'Faculty'})\n- **Department**: {f.get('department') or 'N/A'}"
                if f.get("room"):
                    ans += f"\n- **Room**: {f['room']} ({f.get('block') or 'N/A'})"
                else:
                    ans += f"\n- **Location**: {f.get('block') or 'Campus'} (Room number is not available in the verified faculty data)"
                if f.get("email"):
                    ans += f"\n- **Email**: {f['email']}"
                if f.get("phone"):
                    ans += f"\n- **Phone**: {f['phone']}"
                if f.get("profile_url"):
                    ans += f"\n- **Official Profile**: {f['profile_url']}"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 12. Physical Locations & Blocks (Pharmacy Block, Main Gate, etc.)
        if intent == CampusIntent.LOCATION_LOOKUP:
            res = execute_tool("get_location", query=message)
            if res and res.get("matches"):
                l = res["matches"][0]
                ans = f"**{l['name']}** ({l.get('location_type') or 'Facility'})\n- **Block**: {l.get('block') or 'Campus'}\n- **Floor**: {l.get('floor') or 'N/A'}\n- **Description**: {l.get('description') or 'N/A'}"
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 13. Campus Information (e.g. How many departments are there?)
        if intent == CampusIntent.CAMPUS_INFORMATION_REQUEST:
            if "department" in norm_msg:
                res = execute_tool("search_department", query="")
                count = res.get("count", 18)
                ans = f"VIGNAN University offers **{count} academic departments**, including Computer Science & Engineering, Information Technology, Electronics & Communication, Biotechnology, Mechanical Engineering, and more."
                return self._build_chat_response(ans, executed_tools, tool_records)

        # 14. Fallback multi-tool search
        for fallback_tool, kw in [
            ("search_department", {"query": message}),
            ("search_service", {"query": message}),
            ("search_office", {"query": message}),
            ("search_responsibility", {"query": message}),
            ("search_faculty", {"query": message}),
            ("get_location", {"query": message}),
        ]:
            res = execute_tool(fallback_tool, **kw)
            if res and res.get("matches"):
                m = res["matches"][0]
                name = m.get("name") or m.get("full_name") or m.get("person_name") or "Campus Entity"
                desc = m.get("description") or m.get("responsibilities") or m.get("purpose") or ""
                block = m.get("block") or (m.get("location") or {}).get("block") or "Campus"
                room = m.get("room") or "N/A"
                ans = f"**{name}**\n- **Location**: {block} (Room: {room})\n- **Details**: {desc}"
                return self._build_chat_response(ans, executed_tools, tool_records)

        ans = "I checked the official campus database, but no verified records were found matching your query."
        return self._build_chat_response(ans, executed_tools, tool_records)

    def _build_chat_response(
        self,
        answer: str,
        executed_tools: List[str],
        tool_records: List[ToolCallRecord],
    ) -> ChatResponse:
        """Construct structured ChatResponse with provenance metadata, location, and route details."""
        all_provenance = []
        has_high_confidence = False
        requires_clarification = False
        route_detail: Optional[RouteDetail] = None
        location_detail: Optional[LocationDetail] = None
        live_status_detail: Optional[LiveStatusDetail] = None

        for tr in tool_records:
            res = tr.result
            if isinstance(res, dict):
                if res.get("requires_clarification"):
                    requires_clarification = True
                matches = res.get("matches", [])
                for m in matches:
                    if isinstance(m, dict) and m.get("provenance"):
                        all_provenance.append(m["provenance"])
                    if isinstance(m, dict) and m.get("confidence") == "high":
                        has_high_confidence = True

                # Extract Route details if get_route was called
                if tr.tool_name == "get_route" and res.get("found"):
                    route_detail = RouteDetail(
                        origin=res.get("origin") or res.get("start_location"),
                        destination=res.get("destination") or res.get("destination_location"),
                        start_location=res.get("start_location"),
                        destination_location=res.get("destination_location"),
                        travel_mode=res.get("travel_mode", "walking"),
                        google_maps_url=res.get("google_maps_url"),
                        embedded_map_available=res.get("embedded_map_available", False),
                        embedded_map_url=res.get("embedded_map_url"),
                        indoor_guidance=res.get("indoor_guidance"),
                        steps=[RouteStep(step=s["step"], instruction=s["instruction"]) for s in res.get("steps", []) if isinstance(s, dict)],
                        estimated_minutes=res.get("estimated_minutes"),
                    )

                # Extract Live status details
                if tr.tool_name == "get_live_status" and res.get("current_status"):
                    cs = res["current_status"]
                    live_status_detail = LiveStatusDetail(
                        service_id=res.get("service_id", ""),
                        status=cs.get("status", "active"),
                        queue_length=cs.get("queue_length", 0),
                        estimated_wait_minutes=cs.get("estimated_wait_minutes"),
                        is_expired=cs.get("is_expired", False),
                        recorded_at=cs.get("recorded_at"),
                    )

        confidence = "high" if has_high_confidence or executed_tools else "medium"

        sources = [
            SourceMetadata(
                source_id=p.get("source_id"),
                source_type=p.get("source_type"),
                source_name=p.get("source_name"),
                document_name=p.get("document_name"),
                confidence=p.get("confidence", "high"),
                last_verified=p.get("last_verified")
            )
            for p in all_provenance if isinstance(p, dict)
        ]

        return ChatResponse(
            answer=answer,
            confidence=confidence,
            requires_clarification=requires_clarification,
            tool_used=executed_tools,
            tool_calls=tool_records,
            sources=sources,
            route=route_detail,
            location=location_detail,
            live_status=live_status_detail,
        )


coordinator_agent = CoordinatorAgent()
coordinator = coordinator_agent
