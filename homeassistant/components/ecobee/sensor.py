"""Support for Ecobee sensors."""
from __future__ import annotations

from pyecobee.const import ECOBEE_STATE_CALIBRATING, ECOBEE_STATE_UNKNOWN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_FAHRENHEIT, CONCENTRATION_PARTS_PER_MILLION, CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ECOBEE_MODEL_TO_NAME, MANUFACTURER

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key = "temperature",
        name = "Temperature",
        native_unit_of_measurement = TEMP_FAHRENHEIT,
        device_class = SensorDeviceClass.TEMPERATURE,
        state_class = SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key = "humidity",
        name = "Humidity",
        native_unit_of_measurement = PERCENTAGE,
        device_class = SensorDeviceClass.HUMIDITY,
        state_class = SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key = "co2PPM",
        name = "CO2",
        native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION,
        device_class = SensorDeviceClass.CO2,
        state_class = SensorStateClass.MEASUREMENT,
     ),
    SensorEntityDescription(
        key = "vocPPM",
        name = "VOC",
        device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class = SensorStateClass.MEASUREMENT,
     ),
    SensorEntityDescription(
        key = "airQuality",
        name = "Air Quality Index",
        device_class = SensorDeviceClass.AQI,
        native_unit_of_measurement = None,
        state_class = SensorStateClass.MEASUREMENT
     )
)

runtimeKeys = {
   "temperature" : 'actualTemperature',
   "humidity" : 'actualHumidity',
   "co2PPM" : 'actualCO2',
   "vocPPM" : 'actualVOC',
   "airQuality" : 'actualAQScore'
}
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecobee (temperature and humidity) sensors."""
    data = hass.data[DOMAIN]
    entities = [
        EcobeeSensor(data, sensor["name"], index, description)
        for index in range(len(data.ecobee.thermostats))
        for sensor in data.ecobee.get_remote_sensors(index)
        for item in sensor["capability"]
        for description in SENSOR_TYPES
        if description.key == item["type"]
    ]

    async_add_entities(entities, True)


class EcobeeSensor(SensorEntity):
    """Representation of an Ecobee sensor."""

    def __init__(
        self, data, sensor_name, sensor_index, description: SensorEntityDescription
    ):
        """Initialize the sensor."""
        self.entity_description = description
        self.data = data
        self.sensor_name = sensor_name
        self.index = sensor_index
        self._state = None
        self.thermostat = self.data.ecobee.get_thermostat(self.index)
        self._attr_name = f"{sensor_name} {description.name}"

    @property
    def unique_id(self):
        """Return a unique identifier for this sensor."""
        for sensor in self.data.ecobee.get_remote_sensors(self.index):
            if sensor["name"] == self.sensor_name:
                if "code" in sensor:
                    return f"{sensor['code']}-{self.device_class}"
                return f"{self.thermostat['identifier']}-{sensor['id']}-{self.device_class}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information for this sensor."""
        identifier = None
        model = None
        for sensor in self.data.ecobee.get_remote_sensors(self.index):
            if sensor["name"] != self.sensor_name:
                continue
            if "code" in sensor:
                identifier = sensor["code"]
                model = "ecobee Room Sensor"
            else:
                identifier = self.thermostat["identifier"]
                try:
                    model = (
                        f"{ECOBEE_MODEL_TO_NAME[self.thermostat['modelNumber']]} Thermostat"
                    )
                except KeyError:
                    # Ecobee model is not in our list
                    model = None
            break

        if identifier is not None and model is not None:
            return DeviceInfo(
                identifiers={(DOMAIN, identifier)},
                manufacturer=MANUFACTURER,
                model=model,
                name=self.sensor_name,
            )
        return None

    @property
    def available(self):
        """Return true if device is available."""
        return self.thermostat["runtime"]["connected"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._state in (
            ECOBEE_STATE_CALIBRATING,
            ECOBEE_STATE_UNKNOWN,
            "unknown",
        ):
            return None

        if self.entity_description.key == "temperature":
            return float(self._state) / 10

        return self._state

    async def async_update(self):
        """Get the latest state of the sensor."""
        await self.data.update()
        for sensor in self.data.ecobee.get_remote_sensors(self.index):
            if sensor["name"] != self.sensor_name:
                continue
            for item in sensor["capability"]:
                if item["type"] != self.entity_description.key:
                    continue
                thermostat = self.data.ecobee.get_thermostat(self.index)
                self._state=thermostat["runtime"][runtimeKeys[self.entity_description.key]]
                break
