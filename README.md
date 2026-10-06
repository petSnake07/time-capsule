# TimeCapsule Web App

## Source structure

- `index.html` — page markup and route shells
- `styles.css` — shared responsive styling and themes
- `app.js` — navigation, authentication demo flow, scrapbook editing, media import, drawing, recording, groups, events, and local persistence
- `dist/` — deployable static output with the same flat file layout
- `.openai/hosting.json` — Site hosting configuration

## Routes

- `#landing`
- `#login`
- `#create-account`
- `#verify`
- `#app`

The current account flow is a local browser demonstration. Connect Firebase Auth and a shared database before treating it as production authentication or multi-user storage.
