from mock_tire_pressure import NORMAL_KPA, SIGNALS, TirePressureMock


def test_values_are_whole_numbers():
    tire = TirePressureMock(seed=1)
    assert all(isinstance(tire.next_value(), int) for _ in range(100))


def test_values_stay_near_normal():
    tire = TirePressureMock(seed=2)
    assert all(abs(tire.next_value() - NORMAL_KPA) < 20 for _ in range(1000))


def test_values_change():
    tire = TirePressureMock(seed=3)
    assert len({tire.next_value() for _ in range(50)}) > 1


def test_four_tires():
    assert len(set(SIGNALS.values())) == 4
