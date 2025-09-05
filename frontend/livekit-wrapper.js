// LiveKit Client Wrapper
// This creates a proper global LiveKit object from the ES modules

import * as LiveKitSDK from 'https://cdn.skypack.dev/livekit-client@1.15.13';

// Expose LiveKit globally
window.LiveKit = LiveKitSDK;

console.log('LiveKit wrapper loaded, global object created:', LiveKitSDK);
