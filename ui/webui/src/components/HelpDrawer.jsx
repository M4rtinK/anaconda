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
import React, { useRef } from "react";
import {
    Drawer,
    DrawerActions,
    DrawerCloseButton,
    DrawerContent,
    DrawerContentBody,
    DrawerHead,
    DrawerPanelContent,
    Text,
    TextContent,
    TextVariants,
    Title
} from "@patternfly/react-core";

export const HelpDrawer = ({ isExpanded, setIsExpanded, children }) => {
    const drawerRef = useRef(null);

    const onExpand = () => {
        drawerRef.current && drawerRef.current.focus();
    };

    const onCloseClick = () => {
        setIsExpanded(false);
    };

    // FIXME: Replace the placeholder text.
    const content = (
        <TextContent>
            <Title headingLevel="h2">
                Storage options
            </Title>
            <Text component={TextVariants.p}>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
                tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
                veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex
                ea commodo consequat.
            </Text>
            <Text component={TextVariants.p}>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
                tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
                veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex
                ea commodo consequat.
            </Text>
        </TextContent>
    );

    const panelContent = (
        <DrawerPanelContent isResizable defaultSize="450px" minSize="150px">
            <DrawerHead>
                <span tabIndex={isExpanded ? 0 : -1} ref={drawerRef}>
                    {content}
                </span>
                <DrawerActions>
                    <DrawerCloseButton onClick={onCloseClick} />
                </DrawerActions>
            </DrawerHead>
        </DrawerPanelContent>
    );

    return (
        <Drawer isExpanded={isExpanded} position="right" onExpand={onExpand}>
            <DrawerContent panelContent={panelContent}>
                <DrawerContentBody>{children}</DrawerContentBody>
            </DrawerContent>
        </Drawer>

    );
};
