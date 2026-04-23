
import asyncio
import inspect
import re

class AgentState:
    # Define possible states for the agent
    ACTIVE = "Active"
    IDLE = "Idle"
    ERROR = "Error"
    HIBERNATION = "Hibernation"

    def __init__(self, initial_state=IDLE):
        if initial_state not in [self.ACTIVE, self.IDLE, self.ERROR, self.HIBERNATION]:
            raise ValueError(f"Invalid initial state: {initial_state}")
        self._current_state = initial_state
        self._state_callbacks = {}
        self._valid_transitions = {
            self.IDLE: [self.ACTIVE, self.HIBERNATION],
            self.ACTIVE: [self.IDLE, self.ERROR, self.HIBERNATION],
            self.ERROR: [self.IDLE, self.HIBERNATION],
            self.HIBERNATION: [self.IDLE]
        }
        print(f"Agent initialized in state: {self._current_state}")

    @property
    def current_state(self):
        return self._current_state

    def register_callback(self, state, callback_func):
        all_known_states = set(self._valid_transitions.keys())
        for transitions in self._valid_transitions.values():
            all_known_states.update(transitions)

        if state not in all_known_states:
            raise ValueError(f"Invalid state for callback registration: {state}. Known states are: {sorted(list(all_known_states))}")
        self._state_callbacks[state] = callback_func
        print(f"Callback registered for state: {state}")

    async def transition_to(self, new_state):
        if new_state not in self._valid_transitions.get(self._current_state, []):
            print(f"Invalid state transition from {self._current_state} to {new_state}")
            return False

        self._current_state = new_state
        print(f"Agent transitioned to state: {self._current_state}")

        if new_state in self._state_callbacks:
            print(f"Executing callback for state: {new_state}")
            callback_func = self._state_callbacks[new_state]
            if inspect.iscoroutinefunction(callback_func):
                await callback_func()
            else:
                callback_func()
        return True

    def __str__(self):
        return f"Agent is currently {self._current_state}"


class MonitoringAgent(AgentState):
    ALERTING = "Alerting"

    def __init__(self, initial_state=AgentState.IDLE):
        super().__init__(initial_state)
        print(f"MonitoringAgent initialized. Current state: {self.current_state}")
        self._valid_transitions[self.ACTIVE].append(self.ALERTING)
        self._valid_transitions[self.ALERTING] = [self.ACTIVE, self.IDLE, self.HIBERNATION, self.ERROR]

    async def monitor_system(self):
        print("Monitoring system for anomalies...")
        await asyncio.sleep(0.2)
        if self.current_state == AgentState.ACTIVE:
            print("System is stable, continuing active monitoring.")
        elif self.current_state == self.ALERTING:
            print("System is in alerting state, taking corrective actions.")
        else:
            print("Monitoring agent is not active or alerting, skipping monitoring cycle.")

    async def trigger_alert(self):
        if await self.transition_to(self.ALERTING):
            print("!!! ALERT: Anomaly detected! Entering Alerting state. !!!")
        else:
            print(f"Could not transition to Alerting from {self.current_state}.")

    async def resolve_alert(self):
        if await self.transition_to(AgentState.ACTIVE):
            print("Alert resolved. Returning to Active state.")
        else:
            print(f"Could not resolve alert from {self.current_state}.")


class NegotiationAgent(AgentState):
    PROPOSING = "Proposing"
    EVALUATING = "Evaluating"
    BARGAINING = "Bargaining"
    AGREED = "Agreed"
    REJECTED = "Rejected"
    HUMAN_INTERVENTION = "HumanIntervention"

    def __init__(self, initial_state=AgentState.IDLE, initial_offer=0):
        super().__init__(initial_state)
        print(f"NegotiationAgent initialized. Current state: {self.current_state}")
        self._current_offer = initial_offer
        self._last_user_response = None
        self._negotiation_history = []
        self._last_proposed_offer = initial_offer
        self._last_negotiation_outcome = None

        self._valid_transitions[self.ACTIVE].extend([self.PROPOSING, self.AGREED, self.REJECTED, self.HUMAN_INTERVENTION])
        self._valid_transitions[self.PROPOSING] = [self.EVALUATING, self.BARGAINING, self.AGREED, self.REJECTED, self.ERROR, self.HIBERNATION, self.HUMAN_INTERVENTION]
        self._valid_transitions[self.EVALUATING] = [self.PROPOSING, self.BARGAINING, self.AGREED, self.REJECTED, self.ERROR, self.HIBERNATION, self.HUMAN_INTERVENTION]
        self._valid_transitions[self.BARGAINING] = [self.PROPOSING, self.EVALUATING, self.AGREED, self.REJECTED, self.ERROR, self.HIBERNATION, self.HUMAN_INTERVENTION]
        self._valid_transitions[self.AGREED] = [self.IDLE, self.HIBERNATION]
        self._valid_transitions[self.REJECTED] = [self.IDLE, self.HIBERNATION, self.BARGAINING, self.PROPOSING, self.HUMAN_INTERVENTION]
        self._valid_transitions[self.ERROR].append(self.HUMAN_INTERVENTION)
        self._valid_transitions[self.HUMAN_INTERVENTION] = [self.IDLE, self.PROPOSING, self.BARGAINING]

    async def propose_offer(self, offer_amount):
        if self.current_state == self.PROPOSING:
            self._current_offer = offer_amount
            self._last_proposed_offer = offer_amount
            print(f"Agent re-proposes an offer of: ${offer_amount} (already in PROPOSING state).")
            return True

        if await self.transition_to(self.PROPOSING):
            self._current_offer = offer_amount
            self._last_proposed_offer = offer_amount
            print(f"Agent proposes an offer of: ${offer_amount}")
            return True
        else:
            print(f"Could not propose offer from {self.current_state}.")
            return False

    async def evaluate_user_response(self, user_response):
        if not await self.transition_to(self.EVALUATING):
            print(f"Could not evaluate user response from {self.current_state}.")
            return

        self._last_user_response = user_response
        print(f"Agent evaluating user response: '{user_response}'")
        await asyncio.sleep(0.5)
        outcome = None

        user_response_lower = user_response.lower()
        print(f"DEBUG: Processed user response (lower): '{user_response_lower}'")

        # --- Refined Evaluation Logic ---
        # Updated reject_keywords to include 'cannot accept' or similar strong rejections.
        reject_keywords = r'\b(reject|no|too high|too expensive|can\'t take|not accepted|no way|unreasonable|cannot negotiate|leaving|cannot accept)\b'
        print(f"DEBUG: reject_keywords: '{reject_keywords}'")
        reject_match = re.search(reject_keywords, user_response_lower)
        print(f"DEBUG: reject_match result: {reject_match}")

        if reject_match:
            print(f"DEBUG: Rejection matched: '{reject_match.group(0)}'")
            print("User rejected the offer.")
            outcome = self.REJECTED
            await self.transition_to(self.REJECTED)
        else:
            accept_keywords = r'\b(accept|deal|agree|ok|okay|yes)\b'
            take_it_keyword = r'\btake it\b'
            negation_keywords = r'\b(not|n\'t|cant|can\'t|don\'t)\b'

            is_acceptance = False
            if accept_match_strong := re.search(accept_keywords, user_response_lower):
                if not (negation_match := re.search(negation_keywords, user_response_lower)) or accept_match_strong.start() > negation_match.end():
                    is_acceptance = True
            elif take_it_match := re.search(take_it_keyword, user_response_lower):
                if not re.search(negation_keywords, user_response_lower):
                    is_acceptance = True

            if is_acceptance:
                print(f"DEBUG: Acceptance detected.")
                print("User accepted the offer!")
                outcome = self.AGREED
                await self.transition_to(self.AGREED)
            else:
                number_match = re.search(r'(\d+)', user_response_lower)
                bargain_keywords = r'\b(counter|higher|lower|how about|what about|negotiate|bit lower|price)\b'
                bargain_match = re.search(bargain_keywords, user_response_lower)

                if number_match or bargain_match:
                    print(f"DEBUG: Bargaining detected (number: {number_match is not None}, keywords: {bargain_match is not None}).")
                    print("User wants to bargain.")
                    outcome = self.BARGAINING
                    await self.transition_to(self.BARGAINING)
                else:
                    print("DEBUG: No specific match, treating as bargaining to re-engage.")
                    outcome = self.BARGAINING
                    await self.transition_to(self.BARGAINING)

        self._negotiation_history.append({
            'offer': self._last_proposed_offer,
            'user_response': user_response,
            'outcome': outcome
        })
        self._last_negotiation_outcome = outcome

    async def _calculate_next_offer(self):
        if not self._negotiation_history:
            return self._last_proposed_offer * 0.9

        last_interaction = self._negotiation_history[-1]
        last_offer = last_interaction['offer']
        last_outcome = last_interaction['outcome']
        user_response_text = last_interaction['user_response']

        if last_outcome == self.REJECTED:
            new_offer = last_offer * 0.8
            print(f"Strategy: Last offer was rejected. Proposing a significantly lower offer.")
        elif last_outcome == self.BARGAINING:
            if match := re.search(r'(\d+)', user_response_text):
                user_counter = float(match.group(1))
                new_offer = (last_offer + user_counter) / 2
                print(f"Strategy: User countered to {user_counter}. Meeting halfway.")
            else:
                new_offer = last_offer * 0.95
                print(f"Strategy: User wants to bargain, but no specific counter. Making a moderate reduction.")
        else:
            new_offer = last_offer * 0.9

        return max(1, round(new_offer))

    async def bargain(self, new_offer=None):
        should_proceed_with_bargaining = False
        if self.current_state == self.BARGAINING:
            should_proceed_with_bargaining = True
        else:
            should_proceed_with_bargaining = await self.transition_to(self.BARGAINING)

        if should_proceed_with_bargaining:
            if new_offer:
                self._current_offer = new_offer
                print(f"Agent counter-proposes (explicitly): ${new_offer}")
            else:
                calculated_offer = await self._calculate_next_offer()
                self._current_offer = calculated_offer
                self._last_proposed_offer = calculated_offer
                print(f"Agent counter-proposes (strategically): ${calculated_offer}")
        else:
            print(f"Could not perform bargaining action from {self.current_state}.")

    async def trigger_human_intervention(self, reason="Unknown reason for human intervention."):
        print(f"DEBUG: Attempting to trigger human intervention from {self.current_state}")
        if await self.transition_to(self.HUMAN_INTERVENTION):
            print(f"DEBUG: Successfully transitioned to {self.current_state}")
            print(f"!!! Human Intervention Required: {reason} !!!")
        else:
            print(f"Could not trigger human intervention from {self.current_state}.")

    async def resolve_human_intervention(self, new_state_after_intervention=AgentState.IDLE):
        if self.current_state == self.HUMAN_INTERVENTION:
            print(f"Human intervention resolved. Transitioning to {new_state_after_intervention}.")
            await self.transition_to(new_state_after_intervention)
        else:
            print(f"Not in Human Intervention state. Current state: {self.current_state}.")

    async def conclude_negotiation(self):
        if self.current_state == self.AGREED:
            print(f"Negotiation concluded successfully with offer: ${self._current_offer}")
            await self.transition_to(self.IDLE)
        elif self.current_state == self.REJECTED:
            print("Negotiation concluded with rejection.")
            await self.transition_to(self.IDLE)
        else:
            print(f"Negotiation cannot be concluded in current state: {self.current_state}.")
            if not await self.transition_to(self.IDLE):
                await self.transition_to(self.ERROR)

        self._negotiation_history = []
        self._last_proposed_offer = 0
        self._last_negotiation_outcome = None


class AgentFactory:
    def __init__(self):
        self._agents = {}

    def register_agent(self, type_name, agent_class):
        if not issubclass(agent_class, AgentState):
            raise ValueError(f"Class {agent_class.__name__} must inherit from AgentState")
        self._agents[type_name] = agent_class
        print(f"Agent type '{type_name}' registered: {agent_class.__name__}")

    def create_agent(self, type_name, initial_state=AgentState.IDLE):
        agent_class = self._agents.get(type_name)
        if not agent_class:
            raise ValueError(f"Agent type '{type_name}' is not registered.")
        print(f"Creating instance of {agent_class.__name__} with initial state {initial_state}.")
        return agent_class(initial_state=initial_state)
