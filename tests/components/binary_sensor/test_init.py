"""The tests for the Binary sensor component."""
from collections.abc import Generator
from unittest import mock

import pytest

from homeassistant.components import binary_sensor
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    help_test_all,
    import_and_test_deprecated_constant_enum,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.testing_config.custom_components.test.binary_sensor import MockBinarySensor

TEST_DOMAIN = "test"


def test_state() -> None:
    """Test binary sensor state."""
    sensor = binary_sensor.BinarySensorEntity()
    assert sensor.state is None
    with mock.patch(
        "homeassistant.components.binary_sensor.BinarySensorEntity.is_on",
        new=False,
    ):
        assert binary_sensor.BinarySensorEntity().state == STATE_OFF
    with mock.patch(
        "homeassistant.components.binary_sensor.BinarySensorEntity.is_on",
        new=True,
    ):
        assert binary_sensor.BinarySensorEntity().state == STATE_ON


class MockFlow(ConfigFlow):
    """Test flow."""


@pytest.fixture(autouse=True)
def config_flow_fixture(hass: HomeAssistant) -> Generator[None, None, None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    with mock_config_flow(TEST_DOMAIN, MockFlow):
        yield


async def test_name(hass: HomeAssistant) -> None:
    """Test binary sensor name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setup(
            config_entry, binary_sensor.DOMAIN
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
        ),
    )

    # Unnamed binary sensor without device class -> no name
    entity1 = binary_sensor.BinarySensorEntity()
    entity1.entity_id = "binary_sensor.test1"

    # Unnamed binary sensor with device class but has_entity_name False -> no name
    entity2 = binary_sensor.BinarySensorEntity()
    entity2.entity_id = "binary_sensor.test2"
    entity2._attr_device_class = binary_sensor.BinarySensorDeviceClass.BATTERY

    # Unnamed binary sensor with device class and has_entity_name True -> named
    entity3 = binary_sensor.BinarySensorEntity()
    entity3.entity_id = "binary_sensor.test3"
    entity3._attr_device_class = binary_sensor.BinarySensorDeviceClass.BATTERY
    entity3._attr_has_entity_name = True

    # Unnamed binary sensor with device class and has_entity_name True -> named
    entity4 = binary_sensor.BinarySensorEntity()
    entity4.entity_id = "binary_sensor.test4"
    entity4.entity_description = binary_sensor.BinarySensorEntityDescription(
        "test",
        binary_sensor.BinarySensorDeviceClass.BATTERY,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Set up test binary_sensor platform via config entry."""
        async_add_entities([entity1, entity2, entity3, entity4])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{binary_sensor.DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity1.entity_id)
    assert state.attributes == {}

    state = hass.states.get(entity2.entity_id)
    assert state.attributes == {"device_class": "battery"}

    state = hass.states.get(entity3.entity_id)
    assert state.attributes == {"device_class": "battery", "friendly_name": "Battery"}

    state = hass.states.get(entity4.entity_id)
    assert state.attributes == {"device_class": "battery", "friendly_name": "Battery"}


sensor3_icon = "mdi:binary_sensor3"
sensor4_icon = "mdi:binary_sensor4"
sensor5_icon = "mdi:binary_sensor5"
sensor6_icon = "mdi:binary_sensor6"


class BinarySensorNoDefaultIcon(binary_sensor.BinarySensorEntity):
    """Test binary sensor with no icon."""

    def __init__(
        self, binary_sensor_device_class: binary_sensor.BinarySensorDeviceClass
    ) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._is_on: bool | None = None
        self.device_class = binary_sensor_device_class

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self._is_on

    def turn_on(self) -> None:
        """Turn the entity on."""
        self._is_on = True

    def turn_off(self) -> None:
        """Turn the entity off."""
        self._is_on = False


class BinarySensorNoDefaultIconIsOnAttr(binary_sensor.BinarySensorEntity):
    """Test binary sensor with no icon."""

    def __init__(
        self, binary_sensor_device_class: binary_sensor.BinarySensorDeviceClass
    ) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._attr_is_on = None
        self.device_class = binary_sensor_device_class

    def turn_on(self) -> None:
        """Turn the entity on."""
        self._attr_is_on = True

    def turn_off(self) -> None:
        """Turn the entity off."""
        self._attr_is_on = False


class BinarySensorWithIcon(BinarySensorNoDefaultIcon):
    """Test binary sensor with icon."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return sensor3_icon


class BinarySensorWithIconIsOnAttr(BinarySensorNoDefaultIconIsOnAttr):
    """Test binary sensor with icon."""

    @property
    def icon(self) -> str:
        """Return the icon."""
        return sensor4_icon


class BinarySensorWithIconAttr(BinarySensorNoDefaultIcon):
    """Test binary sensor with icon."""

    def __init__(
        self, binary_sensor_device_class: binary_sensor.BinarySensorDeviceClass
    ) -> None:
        """Initialize the sensor."""
        super().__init__(binary_sensor_device_class)
        self._attr_icon = sensor5_icon


class BinarySensorWithIconAttrIsOnAttr(BinarySensorNoDefaultIconIsOnAttr):
    """Test binary sensor with icon."""

    def __init__(
        self, binary_sensor_device_class: binary_sensor.BinarySensorDeviceClass
    ) -> None:
        """Initialize the sensor."""
        super().__init__(binary_sensor_device_class)
        self._attr_icon = sensor6_icon


@pytest.mark.parametrize(
    "device_class", list(binary_sensor.BinarySensorDeviceClass) + [None]
)
async def test_default_icon(
    device_class: binary_sensor.BinarySensorDeviceClass, hass: HomeAssistant
) -> None:
    """Test binary sensor default icon."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setup(
            config_entry, binary_sensor.DOMAIN
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
        ),
    )

    entity1 = BinarySensorNoDefaultIcon(device_class)
    entity2 = BinarySensorNoDefaultIconIsOnAttr(device_class)
    entity3 = BinarySensorWithIcon(device_class)
    entity4 = BinarySensorWithIconIsOnAttr(device_class)
    entity5 = BinarySensorWithIconAttr(device_class)
    entity6 = BinarySensorWithIconAttrIsOnAttr(device_class)

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Set up test binary_sensor platform via config entry."""
        async_add_entities([entity1, entity2, entity3, entity4, entity5, entity6])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{binary_sensor.DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert entity1.icon is None
    assert entity2.icon is None
    assert entity3.icon == sensor3_icon
    assert entity4.icon == sensor4_icon
    assert entity5.icon == sensor5_icon
    assert entity6.icon == sensor6_icon
    # run twice to make sure when state changes it updates icon each time
    for _ in range(2):
        entity1.turn_on()
        entity2.turn_on()
        entity3.turn_on()
        entity4.turn_on()
        entity5.turn_on()
        entity6.turn_on()
        if device_class is None:
            assert entity1.icon is None
            assert entity2.icon is None
        else:
            assert entity1.icon == binary_sensor.DEVICE_ICON_MAP[device_class][0]
            assert entity2.icon == binary_sensor.DEVICE_ICON_MAP[device_class][0]
        assert entity3.icon == sensor3_icon
        assert entity4.icon == sensor4_icon
        assert entity5.icon == sensor5_icon
        assert entity6.icon == sensor6_icon
        entity1.turn_off()
        entity2.turn_off()
        entity3.turn_off()
        if device_class is None:
            assert entity1.icon is None
            assert entity2.icon is None
        else:
            assert entity1.icon == binary_sensor.DEVICE_ICON_MAP[device_class][1]
            assert entity2.icon == binary_sensor.DEVICE_ICON_MAP[device_class][1]
        assert entity3.icon == sensor3_icon
        assert entity4.icon == sensor4_icon
        assert entity5.icon == sensor5_icon
        assert entity6.icon == sensor6_icon

        # reset entities with no default icon to is_on = None
        entity1._is_on = None
        entity2._attr_is_on = None
        assert entity1.icon is None
        assert entity2.icon is None


async def test_entity_category_config_raises_error(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test error is raised when entity category is set to config."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setup(
            config_entry, binary_sensor.DOMAIN
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
        ),
    )

    description1 = binary_sensor.BinarySensorEntityDescription(
        "diagnostic", entity_category=EntityCategory.DIAGNOSTIC
    )
    entity1 = MockBinarySensor()
    entity1.entity_description = description1
    entity1.entity_id = "binary_sensor.test1"

    description2 = binary_sensor.BinarySensorEntityDescription(
        "config", entity_category=EntityCategory.CONFIG
    )
    entity2 = MockBinarySensor()
    entity2.entity_description = description2
    entity2.entity_id = "binary_sensor.test2"

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Set up test binary_sensor platform via config entry."""
        async_add_entities([entity1, entity2])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{binary_sensor.DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state1 = hass.states.get("binary_sensor.test1")
    assert state1 is not None
    state2 = hass.states.get("binary_sensor.test2")
    assert state2 is None
    assert (
        "Entity binary_sensor.test2 cannot be added as the entity category is set to config"
        in caplog.text
    )


def test_all() -> None:
    """Test module.__all__ is correctly set."""
    help_test_all(binary_sensor)


@pytest.mark.parametrize(
    "device_class",
    list(binary_sensor.BinarySensorDeviceClass),
)
def test_deprecated_constant_device_class(
    caplog: pytest.LogCaptureFixture,
    device_class: binary_sensor.BinarySensorDeviceClass,
) -> None:
    """Test deprecated binary sensor device classes."""
    import_and_test_deprecated_constant_enum(
        caplog, binary_sensor, device_class, "DEVICE_CLASS_", "2025.1"
    )
