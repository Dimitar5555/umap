import * as L from '../../vendors/leaflet/leaflet-src.esm.js'
import { SyncEngine } from './sync/engine.js'

import URLs from './urls.js'
import * as utils from './utils.js'

// Import modules and export them to the global scope.
// For the not yet module-compatible JS out there.

// Copy the leaflet module, it's expected by leaflet plugins to be writeable.
window.L = { ...L }

window.umap = { URLs, SyncEngine, utils }