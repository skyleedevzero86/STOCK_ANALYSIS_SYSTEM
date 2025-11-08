function generateUrlHash(url) {
    if (!url) return '';
    
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
        const char = url.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    const hashStr = Math.abs(hash).toString(36);
    return hashStr.substring(0, 12);
}

function encodeUrlToBase64(url) {
    try {
        const encoded = btoa(unescape(encodeURIComponent(url)));
        return encoded.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    } catch (e) {
        return encodeURIComponent(url);
    }
}

function decodeUrlFromBase64(encoded) {
    if (!encoded) return '';
    
    try {
        let base64 = encoded.replace(/-/g, '+').replace(/_/g, '/');
        const padding = (4 - (base64.length % 4)) % 4;
        base64 = base64 + '='.repeat(padding);
        
        const binaryString = atob(base64);
        const decoded = decodeURIComponent(escape(binaryString));
        return decoded;
    } catch (e) {
        console.debug('Base64 decode error:', e);
        try {
            return decodeURIComponent(encoded);
        } catch (e2) {
            console.error('URI decode error:', e2);
            return encoded;
        }
    }
}

function createShortNewsId(url) {
    if (!url) return '';
    
    try {
        return encodeUrlToBase64(url);
    } catch (e) {
        return encodeURIComponent(url);
    }
}

function decodeShortNewsId(shortId) {
    if (!shortId) return '';
    
    try {
        const decoded = decodeUrlFromBase64(shortId);
        if (decoded && decoded.length > 0 && decoded.startsWith('http')) {
            return decoded;
        }
    } catch (e) {
        console.debug('Base64 decode failed, trying URI decode:', e);
    }
    
    try {
        const uriDecoded = decodeURIComponent(shortId);
        if (uriDecoded && uriDecoded.startsWith('http')) {
            return uriDecoded;
        }
    } catch (e2) {
        console.error('URI decode failed:', e2);
    }
    
    return shortId;
}

