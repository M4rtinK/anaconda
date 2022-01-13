/*
 * Copyright (C) 2022 Red Hat, Inc.
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
import cockpit from 'cockpit';
import React, { useEffect, useContext, useState } from 'react';

import {
    Form,
    FormGroup,
    FormSelect,
    FormSelectOption,
    PageSection,
    Switch,
} from '@patternfly/react-core';

import { AddressContext, Header } from '../Common.jsx';

// This is a wrapper around timedatectl dbus API
import { ServerTime } from 'serverTime';
import { useEvent, useObject } from 'hooks';

export const TimeDate = () => {
    const [timezone, setTimezone] = useState('');
    const [timezones, setTimezones] = useState([]);
    const [useNetworkTime, setUseNetworkTime] = useState(true);
    const address = useContext(AddressContext);

    const timezoneProxy = useObject(() => {
        const client = cockpit.dbus(
            'org.fedoraproject.Anaconda.Modules.Timezone',
            { superuser: 'try', bus: 'none', address }
        );
        const proxy = client.proxy(
            'org.fedoraproject.Anaconda.Modules.Timezone',
            '/org/fedoraproject/Anaconda/Modules/Timezone',
        );
        setTimezone(proxy.Timezone);

        return proxy;
    }, null, [address]);

    useEvent(timezoneProxy, 'changed', (event, data) => {
        setTimezone(data.Timezone);
    });

    const serverTime = useObject(() => new ServerTime(),
                                 st => st.close(),
                                 []);

    useEffect(() => {
        setTimezone(serverTime.get_time_zone());
        serverTime.get_timezones().then(setTimezones, console.error);
    }, [serverTime]);

    const onDoneClicked = () => {
        timezoneProxy.SetTimezone(timezone);
        cockpit.location.go(['summary']);
    };

    return (
        <>
            <Header
              done={onDoneClicked}
              title='Time & Date'
            />
            <PageSection>
                <Form isHorizontal>
                    <Timezones
                      timezone={timezone}
                      timezones={timezones}
                      setTimezone={setTimezone}
                    />
                    <FormGroup
                      fieldId='network-time-switch'
                      hasNoPaddingTop
                      label='Network time'>
                        <Switch
                          id='network-time-switch'
                          isChecked={useNetworkTime}
                          label='Use network time'
                          onChange={setUseNetworkTime}
                        />
                    </FormGroup>
                    <TimeDateManual timedate={serverTime.utc_fake_now} useNetworkTime={useNetworkTime} />
                </Form>
            </PageSection>
        </>
    );
};

const Timezones = ({ timezone, timezones, setTimezone }) => {
    return (
        <FormGroup
          fieldId='timezone-selection'
          label='Timezone'>
            <FormSelect
              id='timezone-selection'
              label='Select timezone'
              value={timezone}
              onChange={setTimezone}
            >
                {timezones.map((option, index) => (
                    <FormSelectOption
                      key={index}
                      value={option}
                      label={option}
                    />
                ))}
            </FormSelect>
        </FormGroup>
    );
};

const TimeDateManual = ({ timedate, useNetworkTime }) => {
    return null;
};
