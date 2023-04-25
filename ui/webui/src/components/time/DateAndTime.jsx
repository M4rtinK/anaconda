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
    ActionGroup,
    Button,
    Card,
    CardTitle,
    CardBody,
    DatePicker,
    Divider,
    Flex,
    FlexItem,
    Form,
    FormGroup,
    FormSection,
    Grid,
    GridItem,
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

import * as timeformat from "timeformat.js";

import { AnacondaPage } from "../AnacondaPage.jsx";

import "./DateAndTime.scss";

import {
    getTimezone,
    setTimezone,
    getTimezones,
    getNTPEnabled,
    setNTPEnabled,
    getSystemDateTime,
    setSystemDateTime,
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
                          {_("pretty region name (pretty timezone name)")}
                      </Text>
                      <Text component={TextVariants.p}>
                          {_("timezone offset")}
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
                                  timezoneName={timezoneName.replaceAll("_", " ")}
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

const EditSettingsCard = ({
    idPrefix,
    setEditModeEnabled,
    automaticTimeEnabled,
    setAutomaticTimeEnabled,
    timezones,
    timezoneName,
    setTimezoneName,
    regionSelected,
    NTPSyncEnabled,
    setNTPSyncEnabled,
    systemDate,
    setSystemDate,
    setNewDate,
}) => {
    const [regionsOpen, setRegionsOpen] = useState(false);
    const [citiesOpen, setCitiesOpen] = useState(false);
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [selectedCity, setSelectedCity] = useState(null);
    const handleRegionChange = (region) => {
        setRegionsOpen(false);
        setSelectedRegion(region);
        // clear city selection if region changes to avoid
        // setting nonsense timezones to the backend
        setSelectedCity(null);
    };
    const handleCityChange = city => {
        setCitiesOpen(false);
        setSelectedCity(city);
    };
    const handleNTPChange = NTPvalue => {
        setNTPSyncEnabled(NTPvalue);
    };
    const handleDateChange = (_event, str, date) => {
        // update the system date with the year, month and day set in the date picker
        const newDate = systemDate;
        newDate.setYear(date.getFullYear());
        newDate.setMonth(date.getMonth());
        newDate.setDate(date.getDate());
        setNewDate(newDate);
    };
    const handleTimeChange = (_event, time, hours, minutes, seconds, isValid) => {
        const newDate = systemDate;
        newDate.setHours(hours);
        newDate.setMinutes(minutes);
        newDate.setSeconds(seconds);
        setNewDate(newDate);
    };
    const handleSave = () => {
        console.log("time & date - saving settings to backend");
        // set NTP on/off
        setAutomaticTimeEnabled(NTPSyncEnabled);
        setNTPEnabled(NTPSyncEnabled);
        console.log("NTP sync set to: " + NTPSyncEnabled);
        // set timezone
        if (selectedRegion && selectedCity) {
            const newTimezoneName = selectedRegion + "/" + selectedCity;
            setTimezoneName(newTimezoneName);
            setTimezone(newTimezoneName);
            console.log("timezone set to: " + newTimezoneName);
        }
        // set date & time
        setSystemDateTime(systemDate.toISOString());
        console.log("system date time set to: " + systemDate.toISOString());
        // finaly disable editing mode
        setEditModeEnabled(false);
    };
    const handleCancel = () => {
        console.log("time & date - cancel editing");
        setEditModeEnabled(false);
    };

    return (
        <Card>
            <CardBody>
                <Form>
                    <FormSection title={_("Timezone")}>
                        <Grid hasGutter>
                            <GridItem span={6}>
                                <FormGroup
                                  label={_("Region")}
                                  isRequired
                                  fieldId="time-date-edit-region"
                                >
                                    <Select
                                      id={idPrefix + "select-region"}
                                      variant={SelectVariant.typeahead}
                                      placeholderText={_("Select region")}
                                      isOpen={regionsOpen}
                                      selections={selectedRegion || timezoneName.split("/")[0]}
                                      onToggle={(_, isOpen) => setRegionsOpen(isOpen)}
                                      onSelect={(event, value) => handleRegionChange(value)}
                                    >
                                        {Object.keys(timezones).map(region => <SelectOption key={region} value={region}>{region}</SelectOption>)}
                                    </Select>
                                </FormGroup>
                            </GridItem>
                            <GridItem span={6}>
                                <FormGroup
                                  label={_("City")}
                                  isRequired
                                  fieldId="time-date-edit-city"
                                >
                                    <Select
                                      id={idPrefix + "select-city"}
                                      variant={SelectVariant.typeahead}
                                      placeholderText={_("Select city")}
                                      isOpen={citiesOpen}
                                      selections={selectedCity || timezoneName.split("/")[1]}
                                      onToggle={(_, isOpen) => setCitiesOpen(isOpen)}
                                      onSelect={(event, value) => handleCityChange(value)}
                                    >
                                        {selectedRegion
                                            ? timezones[selectedRegion].map(city =>
                                                <SelectOption
                                                  key={city}
                                                  value={city}
                                                >
                                                    {city.replaceAll("_", " ")}
                                                </SelectOption>)
                                            : []}
                                    </Select>
                                </FormGroup>
                            </GridItem>
                        </Grid>
                    </FormSection>
                    <FormSection title={_("Date and time")}>
                        <Grid>
                            <GridItem span={4}>
                                <FormGroup
                                  label={_("Automatic time")}
                                  labelIcon={
                                      <Popover
                                        bodyContent={_(
                                            "To edit date and time, turn off automatic time."
                                        )}
                                      >
                                          <Icon iconSize="sm">
                                              <OutlinedQuestionCircleIcon />
                                          </Icon>
                                      </Popover>
                                  }
                                  isRequired
                                  fieldId="time-date-edit-NTP-enabled"
                                >
                                    <Switch
                                      label={_("On")}
                                      labelOff={_("Off")}
                                      id={idPrefix + "switch-automatic-time"}
                                      isChecked={NTPSyncEnabled}
                                      onChange={handleNTPChange}
                                      hasCheckIcon
                                    />
                                </FormGroup>
                            </GridItem>
                            <GridItem span={8}>
                                <Flex
                                  direction={{ default: "row" }}
                                  spaceItems={{ default: "spaceItemsSm" }}
                                >
                                    <FormGroup
                                      label={_("Date")}
                                      isRequired
                                      fieldId="time-date-edit-date"
                                    >
                                        <DatePicker
                                          isDisabled={NTPSyncEnabled}
                                          dateFormat={timeformat.date}
                                          dateParse={timeformat.parseDate}
                                          value={timeformat.date(systemDate.valueOf())}
                                          onChange={handleDateChange}
                                        />
                                    </FormGroup>
                                    <FormGroup
                                      label={_("Time")}
                                      isRequired
                                      fieldId="time-date-edit-time"
                                    >
                                        <TimePicker
                                          isDisabled={NTPSyncEnabled}
                                          time={systemDate}
                                          onChange={handleTimeChange}
                                        />
                                    </FormGroup>
                                </Flex>
                            </GridItem>
                        </Grid>
                    </FormSection>
                    <Divider />
                    <Text className="time-edit-automatic-hint">
                        {_("To edit date and time, turn off automatic time")}
                    </Text>
                    <ActionGroup>
                        <Button
                          id={idPrefix + "-btn-save"}
                          variant="primary"
                          onClick={handleSave}
                        >
                            {_("Save")}
                        </Button>
                        <Button
                          id={idPrefix + "-btn-cancel"}
                          variant="link"
                          onClick={handleCancel}
                        >
                            Cancel
                        </Button>
                    </ActionGroup>
                </Form>
            </CardBody>
        </Card>
    );
};

const AutomaticTimeNotification = ({ automaticTimeEnabled }) => {
    return (
        <Flex direction={{ default: "row" }} spaceItems={{ default: "spaceItemsSm" }} alignSelf={{ default: "alignItemsCenter" }}>
            <FlexItem>
                <Icon status="info">
                    <InfoCircleIcon />
                </Icon>
            </FlexItem>
            <FlexItem>
                <Text className="automatic-time-label">
                    {automaticTimeEnabled ? _("Automatic time is on.") : _("Automatic time is off.")}
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
};

export const DateAndTime = ({ idPrefix }) => {
    // UI modes
    const [editModeEnabled, setEditModeEnabled] = useState(false);
    const [automaticTimeEnabled, setAutomaticTimeEnabled] = useState(true);
    // timezones
    const [timezones, setTimezones] = useState({});
    const [timezoneName, setTimezoneName] = useState("");
    // NTP
    const [NTPSyncEnabled, setNTPSyncEnabled] = useState(true);
    // system time
    const [systemDate, setSystemDate] = useState("");
    const [systemDateString, setSystemDateString] = useState("");
    const [systemTimeString, setSystemTimeString] = useState("");

    // fetch timezone data
    useEffect(() => {
        const fetchTimezoneData = async (setTimezoneName, setTimezones) => {
            const currentTimezone = await getTimezone();
            setTimezoneName(currentTimezone);
            const res = await getTimezones();
            const timezoneDict = res[0];
            setTimezones(timezoneDict);
        };
        fetchTimezoneData(setTimezoneName, setTimezones);
    }, [setTimezoneName, setTimezones]);

    // fetch NTP data
    useEffect(() => {
        const fetchNTPData = async (setAutomaticTimeEnabled) => {
            const NTPEnableValue = await getNTPEnabled();
            setAutomaticTimeEnabled(NTPEnableValue);
        };
        fetchNTPData(setAutomaticTimeEnabled);
    }, [setAutomaticTimeEnabled]);

    // set new date to all the relevant places
    const setNewDate = (newDate) => {
        setSystemDate(newDate);
        // localized display strings
        const localizedDate = newDate.toLocaleString("default", { dateStyle: "full" });
        const localizedTime = newDate.toLocaleString("default", { timeStyle: "short" });
        setSystemDateString(localizedDate);
        setSystemTimeString(localizedTime);
    };

    // fetch system time
    useEffect(() => {
        const fetchSystemDateTime = async (setSystemDate) => {
            const systemDateValue = await getSystemDateTime();
            setSystemDate(systemDateValue[0]);
            // update time
            const newDate = new Date(systemDateValue[0]);
            setNewDate(newDate);
        };
        fetchSystemDateTime(setSystemDate);
    }, [setSystemDate]);

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
                    timezoneName={timezoneName}
                    setTimezoneName={setTimezoneName}
                    NTPSyncEnabled={NTPSyncEnabled}
                    setNTPSyncEnabled={setNTPSyncEnabled}
                    systemDate={systemDate}
                    setSystemDate={setSystemDate}
                    setNewDate={setNewDate}
                />
                : <CurrentSettingsCard
                    idPrefix={idPrefix}
                    timeString={systemTimeString}
                    dateString={systemDateString}
                    setEditModeEnabled={setEditModeEnabled}
                    timezoneName={timezoneName}
                />}
            <AutomaticTimeNotification
              automaticTimeEnabled={automaticTimeEnabled}
            />
        </AnacondaPage>
    );
};
