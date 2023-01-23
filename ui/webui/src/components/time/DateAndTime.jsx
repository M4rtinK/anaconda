/*
 * Copyright (C) 2023 Red Hat, Inc.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with This program; If not, see <http://www.gnu.org/licenses/>.
 */

import React, { useState, useEffect } from "react";

import {
    Button,
    Card,
    CardTitle,
    CardBody,
    DatePicker,
    Divider,
    Flex,
    FlexItem,
    Text,
    TextContent,
    TextVariants,
    TimePicker,
    Popover,
    PopoverPosition,
    Icon,
    Label,
    Switch,
    Select,
    SelectOption,
    SelectVariant,
} from "@patternfly/react-core";

import {
    InfoCircleIcon,
    OutlinedQuestionCircleIcon,
} from "@patternfly/react-icons";

import cockpit from "cockpit";

import { AnacondaPage } from "../AnacondaPage.jsx";

import "./DateAndTime.scss";

import {
    getTimezone,
    getTimezones,
} from "../../apis/timezone.js";

const _ = cockpit.gettext;

const TimezonePopover = ({ timezoneName }) => {
    return (
        <Popover
          position={PopoverPosition.auto}
          bodyContent={
              <Flex>
                  <Flex>
                      <Text component={TextVariants.p}>
                          {_("Timezone")}
                      </Text>
                  </Flex>
                  <Flex spaceItems={{ default: "spaceItemsSm" }}>
                      <Text component={TextVariants.p}>
                          {timezoneName}
                      </Text>
                      <Text component={TextVariants.p}>
                          {_("Americas (New York)")}
                      </Text>
                      <Text component={TextVariants.p}>
                          {_("UTC - 5")}
                      </Text>
                  </Flex>
              </Flex>
          }
        >
            {/* HACK Patternfly currently doesn't implement clickable labels so the styling had to be done manually. */}
            <div style={{ cursor: "pointer", userSelect: "none" }}>
                <Label variant="outline" color="blue" icon={<InfoCircleIcon />} id="betanag-icon"> {timezoneName} </Label>
            </div>
        </Popover>
    );
};

const CurrentSettingsCard = ({ idPrefix, timeString, dateString, setEditModeEnabled, timezoneName }) => {
    return (
        <Card>
            <CardTitle>
                {_("Current settings")}
            </CardTitle>
            <CardBody>
                <Flex direction={{ default: "column" }}>
                    <FlexItem>
                        <Flex direction={{ default: "row" }} alignSelf={{ default: "alignItemsCenter" }}>
                            <FlexItem>
                                <Text className="time-display-label">
                                    {timeString}
                                </Text>
                            </FlexItem>
                            <FlexItem>
                                <TimezonePopover
                                  timezoneName={timezoneName}
                                />
                            </FlexItem>
                        </Flex>
                    </FlexItem>
                    <FlexItem>
                        <Text>
                            {dateString}
                        </Text>
                    </FlexItem>
                    <FlexItem spacer={{ default: "spacerMd" }} />
                    <FlexItem>
                        <Button
                          id={idPrefix + "-edit"}
                          onClick={() => {
                              setEditModeEnabled(true);
                          }}
                          variant="secondary"
                        >
                            {_("Edit")}
                        </Button>
                    </FlexItem>
                </Flex>
            </CardBody>
        </Card>
    );
};

const RegionSelect = ({ regions, selectedRegion, setSelectedRegion }) => {
    const [isOpen, setIsOpen] = useState(false);
    const onToggleClick = () => {
        setIsOpen(!isOpen);
    };
    return (
        <Select
          placeholderText={_("Region")}
          onToggle={onToggleClick}
          onSelect={setSelectedRegion}
          isOpen={isOpen}
          variant={SelectVariant.typeahead}
        >
            {regions.map(region => <SelectOption
              key={region.value}
              value={region} />)}
        </Select>
    );
};

const CitySelect = ({ timezones, regionCities, selectedCity, setSelectedCity }) => {
    const [isOpen, setIsOpen] = useState(false);
    const selectOptions = [
        <SelectOption
          key="foo_key"
          value="foo"
        />,
        <SelectOption
          key="bar_key"
          value="bar"
        />
    ];

    const onToggleClick = () => {
        setIsOpen(!isOpen);
    };
    return (
        <Select
          placeholderText={_("City")}
          variant={SelectVariant.typeahead}
          // selections={selectedCity}
          onToggle={onToggleClick}
          isOpen={isOpen}
          onSelect={setSelectedCity}
        >
            {}
            {regionCities.map(city => <SelectOption
              key={city.value}
              value={city} />)}
        </Select>
    );
};

const EditSettingsCard = ({
    idPrefix,
    setEditModeEnabled,
    automaticTimeEnabled,
    setAutomaticTimeEnabled,
    timezones,
    regions,
    selectedRegion,
    regionSelected,
    regionCities,
    selectedCity,
    setSelectedCity,
}) => {
    return (
        <Card>
            <CardBody>
                <Flex direction={{ default: "column" }} spacer={{ default: "spaceItemsXs" }}>
                    <FlexItem>
                        <Text className="time-edit-heading">
                            {_("Timezone")}
                        </Text>
                    </FlexItem>
                    <FlexItem spacer={{ default: "spacerXs" }} />
                    <FlexItem>
                        <Flex direction={{ default: "row" }} alignSelf={{ default: "alignItemsCenter" }}>
                            <Flex direction={{ default: "column" }}>
                                <FlexItem>
                                    <Text className="time-edit-subheading">
                                        {_("Region")}
                                    </Text>
                                </FlexItem>
                                <FlexItem>
                                    <RegionSelect
                                      regions={regions}
                                      selectedRegion={selectedRegion}
                                      regionSelected={regionSelected}
                                    />
                                </FlexItem>
                            </Flex>
                            <Flex direction={{ default: "column" }}>
                                <FlexItem>
                                    <Text className="time-edit-subheading">
                                        {_("City")}
                                    </Text>
                                </FlexItem>
                                <FlexItem>
                                    <CitySelect
                                      timezones={timezones}
                                      regionCities={regionCities}
                                      selectedCity={selectedCity}
                                      setSelectedCity={setSelectedCity}
                                    />
                                </FlexItem>
                            </Flex>
                        </Flex>
                    </FlexItem>
                    <FlexItem spacer={{ default: "spacerMd" }} />
                    <FlexItem>
                        <Flex direction={{ default: "row" }} alignSelf={{ default: "alignItemsCenter" }}>
                            <Flex direction={{ default: "column" }}>
                                <FlexItem>
                                    <Text className="time-edit-subheading">
                                        {_("Automatic time *")}
                                        <Popover
                                          bodyContent={_(
                                              "To edit date and time, turn off automatric time."
                                          )}
                                        >
                                            <Icon iconSize="sm">
                                                <OutlinedQuestionCircleIcon />
                                            </Icon>
                                        </Popover>
                                    </Text>
                                </FlexItem>
                                <FlexItem>
                                    <Switch
                                      label={_("On")}
                                      labelOff={_("Off")}
                                      id={idPrefix + "switch-automatic-time"}
                                      isChecked={automaticTimeEnabled}
                                      onChange={value => setAutomaticTimeEnabled(value)}
                                      hasCheckIcon
                                    />
                                </FlexItem>
                            </Flex>
                            <Flex direction={{ default: "column" }} spacer={{ default: "spaceItemsXs" }}>
                                <FlexItem>
                                    <Text className="time-edit-subheading">
                                        {_("Date *")}
                                    </Text>
                                </FlexItem>
                                <FlexItem>
                                    <Text>
                                        <DatePicker />
                                    </Text>
                                </FlexItem>
                            </Flex>
                            <Flex direction={{ default: "column" }} spacer={{ default: "spaceItemsXs" }}>
                                <FlexItem>
                                    <Text className="time-edit-subheading">
                                        {_("Time *")}
                                    </Text>
                                </FlexItem>
                                <FlexItem>
                                    <Text>
                                        <TimePicker />
                                    </Text>
                                </FlexItem>
                            </Flex>
                        </Flex>
                    </FlexItem>
                    <FlexItem spacer={{ default: "spacerXs" }} />
                    <Divider />
                    <Text className="time-edit-automatic-hint">
                        {_("To edit date and time, turn off automatic time")}
                    </Text>
                    <FlexItem spacer={{ default: "spacerMd" }} />
                    <Flex direction={{ default: "row" }}>
                        <FlexItem>
                            <Button
                              id={idPrefix + "-btn-save"}
                              onClick={() => {
                                  setEditModeEnabled(false);
                                  // FIXME: COMMIT CHANGES
                              }}
                              variant="primary"
                            >
                                {_("Save")}
                            </Button>
                        </FlexItem>
                        <FlexItem>
                            <Button
                              id={idPrefix + "-btn-cancel"}
                              onClick={() => {
                                  setEditModeEnabled(false);
                              }}
                              variant="link"
                            >
                                {_("Cancel")}
                            </Button>
                        </FlexItem>

                    </Flex>
                </Flex>
            </CardBody>
        </Card>
    );
};

// FIXME: make this dynamic
const automaticTimeNotification = (
    <Flex direction={{ default: "row" }} spaceItems={{ default: "spaceItemsSm" }} alignSelf={{ default: "alignItemsCenter" }}>
        <FlexItem>
            <Icon status="info">
                <InfoCircleIcon />
            </Icon>
        </FlexItem>
        <FlexItem>
            <Text className="automatic-time-label">
                {_("Automatic time is on.")}
            </Text>
        </FlexItem>
        <FlexItem>
            <Popover
              bodyContent={_(
                  "Synchronize your device with Network Time Protocol (NTP) server. " +
                  "You must be connected to the Internet."
              )}
            >
                <Icon iconSize="sm">
                    <OutlinedQuestionCircleIcon />
                </Icon>
            </Popover>
        </FlexItem>
    </Flex>
);

export const DateAndTime = ({ idPrefix }) => {
    // UI modes
    const [editModeEnabled, setEditModeEnabled] = useState(true);
    const [automaticTimeEnabled, setAutomaticTimeEnabled] = useState(true);
    // timezones
    const [timezones, setTimezones] = useState({});
    const [timezoneName, setTimezoneName] = useState("");
    const [regions, setRegions] = useState([]);
    const [selectedRegion, setSelectedRegion] = useState("");
    const [regionCities, setRegioncities] = useState([]);
    const [selectedCity, setSelectedCity] = useState("");
    // NTP
    const [NTPStatus, setNTPStatus] = useState("");
    const [NTPEnabled, setNTPEnabled] = useState(true);
    // system time
    const [systemTime, setSystemTime] = useState("");

    // fetch timezone data
    useEffect(() => {
        const fetchTimezoneData = async (setTimezoneName, setTimezones, setRegions) => {
            const currentTimezone = await getTimezone();
            setTimezoneName(currentTimezone);
            const res = await getTimezones();
            const timezoneDict = res[0];
            setTimezones(timezoneDict);
            // get a list of of regions
            const regions = Object.keys(timezoneDict);
            // sort it
            regions.sort();
            setRegions(regions);
        };
        fetchTimezoneData(setTimezoneName, setTimezones, setRegions);
    }, [setTimezoneName, setTimezones, setRegions]);

    // fetch NTP data

    // fetch system time

    // region selected callback
    const regionSelected = ({ region }) => {
        setSelectedRegion(region);
        setRegions(["A", "B"]);
    };

    return (
        <AnacondaPage title={_("Date and time")}>
            <TextContent>
                <Text id={idPrefix + "-hint"}>
                    {_("The time and date is set automatically, but you can edit it to any time.")}
                </Text>
            </TextContent>
            {editModeEnabled
                ? <EditSettingsCard
                    idPrefix={idPrefix}
                    setEditModeEnabled={setEditModeEnabled}
                    automaticTimeEnabled={automaticTimeEnabled}
                    setAutomaticTimeEnabled={setAutomaticTimeEnabled}
                    timezones={timezones}
                    regions={regions}
                    selectedRegion={selectedRegion}
                    regionCities={regionCities}
                    selectedCity={selectedCity}
                />
                : <CurrentSettingsCard
                    idPrefix={idPrefix}
                    timeString="6:35 AM"
                    dateString="Thursday, November 28, 2022"
                    setEditModeEnabled={setEditModeEnabled}
                    timezoneName={timezoneName}
                />}
            {automaticTimeNotification}
        </AnacondaPage>
    );
};
