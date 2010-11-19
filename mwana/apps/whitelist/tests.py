from rapidsms.tests.scripted import TestScript

class SimpleTest(TestScript):

    def test_trial_period(self):
        script = """
        kb > join
        kb < I'm sorry, Results160 and RemindMi are still in testing phase. We will notify you when the system is live.
        kb > tryout
        kb < You have been granted a 4 hour trial period to test Results160 and RemindMi.
        kb > join
        kb < To register, send JOIN <CLINIC CODE> <NAME> <SECURITY CODE>
    """
        self.runScript(script)
