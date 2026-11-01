from shipready.agent.doctor import DoctorCheck, DoctorReport


def test_doctor_report_is_healthy_only_when_all_checks_pass() -> None:
    healthy = DoctorReport((DoctorCheck("test", True, "ok"),))
    unhealthy = DoctorReport((DoctorCheck("test", False, "missing"),))

    assert healthy.is_healthy
    assert not unhealthy.is_healthy
