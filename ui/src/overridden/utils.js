import React from "react";
import { invenioConfig } from "@inveniosoftware/react-invenio-app-ils";
import { Icon } from "semantic-ui-react";
import _get from "lodash/get";

export const snvLink = (
  <a
    href="https://sis.web.cern.ch/search-and-read/online-resources/snv-connect"
    target="_blank"
    rel="noreferrer"
  >
    SNV-Connect
  </a>
);

export function renderCallNumber(item) {
  const identifiers = _get(item, "identifiers", []);
  if (identifiers === null) {
    return null;
  }
  const callNumber = identifiers.find(
    (identifier) => identifier.scheme === "CALL_NUMBER"
  );
  if (callNumber) {
    return `(${callNumber.value})`;
  }
  return null;
}

export const shelfLink = (shelfNumber, { popupContent = null, iframe = false }) => {
  var shelfLink = `https://maps.web.cern.ch/?n=['SHELF ${shelfNumber}']`;
  if (popupContent !== null) {
    shelfLink = `${shelfLink}&popupContent=${JSON.stringify(popupContent)}`;
  }
  if (iframe) {
    shelfLink = `${shelfLink}&showMenu=false&widgets=&scale=200`;
  }
  return shelfLink;
};

export const shelfLinkComponent = (item, iconName = "map pin") => {
  const shelfNumber = _get(item, "shelf");
  const callNumber = renderCallNumber(item);
  const popupContent = { "Title": item.title, "Call number": callNumber };
  const linkToShelf = shelfLink(shelfNumber, { popupContent: popupContent });
  return (
    <>
      {shelfNumber && (
        <a href={linkToShelf} target="_blank" rel="noreferrer">
          <Icon name={iconName} />
          {shelfNumber}
        </a>
      )}{" "}
      {callNumber}
    </>
  );
};

export function getDisplayVal(configField, value) {
  return _get(invenioConfig, configField).find((entry) => entry.value === value).text;
}
