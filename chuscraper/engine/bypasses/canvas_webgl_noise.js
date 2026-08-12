// Canvas / WebGL fingerprint noise.
//
// The README advertised this bypass but no such file existed, so canvas and
// WebGL fingerprints were going out completely unmodified.
//
// Strategy: a per-session, deterministic sub-pixel perturbation. Deterministic
// matters - a fingerprint that changes on every read inside one session is
// itself a detection signal, so we derive the noise from a session seed and
// apply the same offsets consistently.
(function () {
    try {
        const cfg = window._chuscraper_config || {};

        // Stable per-session seed. Same page = same fingerprint, different
        // session = different fingerprint.
        if (!window.__chu_seed) {
            let s = 0;
            const src = String(cfg.user_agent || '') + String(cfg.screen_width || '');
            for (let i = 0; i < src.length; i++) {
                s = (s * 31 + src.charCodeAt(i)) >>> 0;
            }
            window.__chu_seed = (s ^ 0x9e3779b9) >>> 0;
        }

        const rand = (n) => {
            // xorshift32, seeded per call-site index for reproducibility
            let x = (window.__chu_seed + n * 2654435761) >>> 0;
            x ^= x << 13; x >>>= 0;
            x ^= x >> 17;
            x ^= x << 5; x >>>= 0;
            return x / 4294967296;
        };

        // ---- Canvas 2D / toDataURL -----------------------------------------
        const noisify = (canvas, ctx) => {
            if (!ctx || !canvas || !canvas.width || !canvas.height) return;
            try {
                const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const d = img.data;
                // Perturb a sparse subset of pixels by +/-1 in the low bits:
                // invisible to the eye, fatal to an exact-hash fingerprint.
                for (let i = 0; i < d.length; i += 4 * 977) {
                    const delta = rand(i) < 0.5 ? -1 : 1;
                    d[i] = Math.max(0, Math.min(255, d[i] + delta));
                    d[i + 1] = Math.max(0, Math.min(255, d[i + 1] + delta));
                    d[i + 2] = Math.max(0, Math.min(255, d[i + 2] + delta));
                }
                ctx.putImageData(img, 0, 0);
            } catch (e) { /* tainted canvas (cross-origin) - leave it alone */ }
        };

        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            try { noisify(this, this.getContext('2d')); } catch (e) {}
            return origToDataURL.apply(this, args);
        };

        const origToBlob = HTMLCanvasElement.prototype.toBlob;
        if (origToBlob) {
            HTMLCanvasElement.prototype.toBlob = function (...args) {
                try { noisify(this, this.getContext('2d')); } catch (e) {}
                return origToBlob.apply(this, args);
            };
        }

        const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function (...args) {
            const result = origGetImageData.apply(this, args);
            try {
                const d = result.data;
                for (let i = 0; i < d.length; i += 4 * 977) {
                    const delta = rand(i) < 0.5 ? -1 : 1;
                    d[i] = Math.max(0, Math.min(255, d[i] + delta));
                }
            } catch (e) {}
            return result;
        };

        // ---- WebGL ----------------------------------------------------------
        // UNMASKED_VENDOR_WEBGL / UNMASKED_RENDERER_WEBGL are the two params
        // that leak "SwiftShader" / "Mesa llvmpipe" on headless boxes.
        const UNMASKED_VENDOR = 37445;
        const UNMASKED_RENDERER = 37446;
        const vendor = 'Google Inc. (Intel)';
        const renderer = 'ANGLE (Intel, Intel(R) UHD Graphics (0x00009BC4) Direct3D11 vs_5_0 ps_5_0, D3D11)';

        const patchGL = (proto) => {
            if (!proto || !proto.getParameter) return;
            const orig = proto.getParameter;
            proto.getParameter = function (param) {
                if (param === UNMASKED_VENDOR) return vendor;
                if (param === UNMASKED_RENDERER) return renderer;
                return orig.apply(this, arguments);
            };
            // Keep toString() looking native so a naive
            // Function.prototype.toString check doesn't spot the patch.
            try {
                proto.getParameter.toString = () => 'function getParameter() { [native code] }';
            } catch (e) {}
        };

        if (typeof WebGLRenderingContext !== 'undefined') patchGL(WebGLRenderingContext.prototype);
        if (typeof WebGL2RenderingContext !== 'undefined') patchGL(WebGL2RenderingContext.prototype);

        // Make the patched canvas methods look native too.
        try {
            HTMLCanvasElement.prototype.toDataURL.toString =
                () => 'function toDataURL() { [native code] }';
            CanvasRenderingContext2D.prototype.getImageData.toString =
                () => 'function getImageData() { [native code] }';
        } catch (e) {}
    } catch (e) {
        console.warn(e);
    }
})();
