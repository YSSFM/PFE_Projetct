# ===================================================================
# recognition_state_service.py
# MACHINE D'ÉTAT RECONNAISSANCE
# ===================================================================

import time


class RecognitionState:

    WAITING = "WAITING"
    DETECTED = "DETECTED"
    BLINK_REQUIRED = "BLINK_REQUIRED"
    VERIFIED = "VERIFIED"
    COOLDOWN = "COOLDOWN"


class RecognitionStateMachine:

    def __init__(self):

        self.state = RecognitionState.WAITING

        self.current_student = None

        self.last_verification = 0

        self.cooldown = 10

    # =========================================================
    # STUDENT DETECTED
    # =========================================================

    def student_detected(self, student_id):

        if self.state == RecognitionState.COOLDOWN:

            if time.time() - self.last_verification > self.cooldown:
                self.state = RecognitionState.WAITING

        if self.state == RecognitionState.WAITING:

            self.current_student = student_id

            self.state = RecognitionState.BLINK_REQUIRED

    # =========================================================
    # BLINK VALIDATED
    # =========================================================

    def blink_validated(self):

        if self.state == RecognitionState.BLINK_REQUIRED:

            self.state = RecognitionState.VERIFIED

            self.last_verification = time.time()

            return True

        return False

    # =========================================================
    # START COOLDOWN
    # =========================================================

    def start_cooldown(self):

        self.state = RecognitionState.COOLDOWN

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        self.state = RecognitionState.WAITING

        self.current_student = None