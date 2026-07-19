/**
 * WebGL fluid cursor — colorful ink-in-water diffusion (GPU fluid sim)
 */
(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isMobile = window.innerWidth <= 768;

    if (prefersReducedMotion || isTouchDevice || isMobile) return;

    const canvas = document.getElementById('fluid-cursor-canvas');
    if (!canvas) return;

    const config = {
        SIM_RESOLUTION: 128,
        DYE_RESOLUTION: 1024,
        DENSITY_DISSIPATION: 0.992,
        VELOCITY_DISSIPATION: 0.99,
        PRESSURE: 0.8,
        PRESSURE_ITERATIONS: 20,
        CURL: 32,
        SPLAT_RADIUS: 0.28,
        SPLAT_FORCE: 4800,
        COLOR_UPDATE_SPEED: 10,
    };

    /* Soft pastel ink tones — lime, yellow, coral, lavender, blue, pink */
    const INK_PALETTE = [
        [0.72, 0.95, 0.38],
        [1.0, 0.88, 0.45],
        [1.0, 0.58, 0.48],
        [1.0, 0.72, 0.55],
        [0.78, 0.68, 1.0],
        [0.58, 0.78, 1.0],
        [1.0, 0.62, 0.82],
    ];

    const baseVertexShader = `
        precision highp float;
        attribute vec2 aPosition;
        varying vec2 vUv;
        varying vec2 vL;
        varying vec2 vR;
        varying vec2 vT;
        varying vec2 vB;
        uniform vec2 texelSize;
        void main () {
            vUv = aPosition * 0.5 + 0.5;
            vL = vUv - vec2(texelSize.x, 0.0);
            vR = vUv + vec2(texelSize.x, 0.0);
            vT = vUv + vec2(0.0, texelSize.y);
            vB = vUv - vec2(0.0, texelSize.y);
            gl_Position = vec4(aPosition, 0.0, 1.0);
        }
    `;

    const copyShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        uniform sampler2D uTexture;
        void main () {
            gl_FragColor = texture2D(uTexture, vUv);
        }
    `;

    const clearShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        uniform sampler2D uTexture;
        uniform float value;
        void main () {
            gl_FragColor = value * texture2D(uTexture, vUv);
        }
    `;

    const displayShader = `
        precision highp float;
        precision highp sampler2D;
        varying vec2 vUv;
        uniform sampler2D uTexture;
        void main () {
            vec3 c = texture2D(uTexture, vUv).rgb;
            float a = max(c.r, max(c.g, c.b));
            a = pow(a, 0.85);
            gl_FragColor = vec4(c, a * 0.92);
        }
    `;

    const splatShader = `
        precision highp float;
        precision highp sampler2D;
        varying vec2 vUv;
        uniform sampler2D uTarget;
        uniform float aspectRatio;
        uniform vec3 color;
        uniform vec2 point;
        uniform float radius;
        void main () {
            vec2 p = vUv - point;
            p.x *= aspectRatio;
            vec3 splat = exp(-dot(p, p) / radius) * color;
            vec3 base = texture2D(uTarget, vUv).xyz;
            gl_FragColor = vec4(base + splat, 1.0);
        }
    `;

    const advectionShader = `
        precision highp float;
        precision highp sampler2D;
        varying vec2 vUv;
        uniform sampler2D uVelocity;
        uniform sampler2D uSource;
        uniform vec2 texelSize;
        uniform vec2 dyeTexelSize;
        uniform float dt;
        uniform float dissipation;
        void main () {
            vec2 coord = vUv - dt * texture2D(uVelocity, vUv).xy * texelSize;
            vec4 result = dissipation * texture2D(uSource, coord);
            gl_FragColor = result;
        }
    `;

    const divergenceShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        varying highp vec2 vL;
        varying highp vec2 vR;
        varying highp vec2 vT;
        varying highp vec2 vB;
        uniform sampler2D uVelocity;
        void main () {
            float L = texture2D(uVelocity, vL).x;
            float R = texture2D(uVelocity, vR).x;
            float T = texture2D(uVelocity, vT).y;
            float B = texture2D(uVelocity, vB).y;
            vec2 C = texture2D(uVelocity, vUv).xy;
            if (vL.x < 0.0) L = -C.x;
            if (vR.x > 1.0) R = -C.x;
            if (vT.y > 1.0) T = -C.y;
            if (vB.y < 0.0) B = -C.y;
            float div = 0.5 * (R - L + T - B);
            gl_FragColor = vec4(div, 0.0, 0.0, 1.0);
        }
    `;

    const curlShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        varying highp vec2 vL;
        varying highp vec2 vR;
        varying highp vec2 vT;
        varying highp vec2 vB;
        uniform sampler2D uVelocity;
        void main () {
            float L = texture2D(uVelocity, vL).y;
            float R = texture2D(uVelocity, vR).y;
            float T = texture2D(uVelocity, vT).x;
            float B = texture2D(uVelocity, vB).x;
            float vorticity = R - L - T + B;
            gl_FragColor = vec4(0.5 * vorticity, 0.0, 0.0, 1.0);
        }
    `;

    const vorticityShader = `
        precision highp float;
        precision highp sampler2D;
        varying vec2 vUv;
        varying vec2 vL;
        varying vec2 vR;
        varying vec2 vT;
        varying vec2 vB;
        uniform sampler2D uVelocity;
        uniform sampler2D uCurl;
        uniform float curl;
        uniform float dt;
        void main () {
            float L = texture2D(uCurl, vL).x;
            float R = texture2D(uCurl, vR).x;
            float T = texture2D(uCurl, vT).x;
            float B = texture2D(uCurl, vB).x;
            float C = texture2D(uCurl, vUv).x;
            vec2 force = 0.5 * vec2(abs(T) - abs(B), abs(R) - abs(L));
            force /= length(force) + 0.0001;
            force *= curl * C;
            force.y *= -1.0;
            vec2 velocity = texture2D(uVelocity, vUv).xy;
            velocity += force * dt;
            velocity = min(max(velocity, -1000.0), 1000.0);
            gl_FragColor = vec4(velocity, 0.0, 1.0);
        }
    `;

    const pressureShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        varying highp vec2 vL;
        varying highp vec2 vR;
        varying highp vec2 vT;
        varying highp vec2 vB;
        uniform sampler2D uPressure;
        uniform sampler2D uDivergence;
        void main () {
            float L = texture2D(uPressure, vL).x;
            float R = texture2D(uPressure, vR).x;
            float T = texture2D(uPressure, vT).x;
            float B = texture2D(uPressure, vB).x;
            float C = texture2D(uPressure, vUv).x;
            float divergence = texture2D(uDivergence, vUv).x;
            float pressure = (L + R + B + T - divergence) * 0.25;
            gl_FragColor = vec4(pressure, 0.0, 0.0, 1.0);
        }
    `;

    const gradientSubtractShader = `
        precision mediump float;
        precision mediump sampler2D;
        varying highp vec2 vUv;
        varying highp vec2 vL;
        varying highp vec2 vR;
        varying highp vec2 vT;
        varying highp vec2 vB;
        uniform sampler2D uPressure;
        uniform sampler2D uVelocity;
        void main () {
            float L = texture2D(uPressure, vL).x;
            float R = texture2D(uPressure, vR).x;
            float T = texture2D(uPressure, vT).x;
            float B = texture2D(uPressure, vB).x;
            vec2 velocity = texture2D(uVelocity, vUv).xy;
            velocity.xy -= vec2(R - L, T - B);
            gl_FragColor = vec4(velocity, 0.0, 1.0);
        }
    `;

    function compileShader(type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.warn('Fluid shader compile error:', gl.getShaderInfoLog(shader));
        }
        return shader;
    }

    function createProgram(vert, frag) {
        const program = gl.createProgram();
        gl.attachShader(program, compileShader(gl.VERTEX_SHADER, vert));
        gl.attachShader(program, compileShader(gl.FRAGMENT_SHADER, frag));
        gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            console.warn('Fluid program link error:', gl.getProgramInfoLog(program));
        }
        return program;
    }

    function getUniforms(program) {
        const uniforms = {};
        const count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
        for (let i = 0; i < count; i += 1) {
            const info = gl.getActiveUniform(program, i);
            uniforms[info.name] = gl.getUniformLocation(program, info.name);
        }
        return uniforms;
    }

    function createFBO(w, h, internalFormat, format, type, filter) {
        gl.activeTexture(gl.TEXTURE0);
        const texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, w, h, 0, format, type, null);

        const fbo = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
        gl.viewport(0, 0, w, h);
        gl.clear(gl.COLOR_BUFFER_BIT);

        return {
            texture,
            fbo,
            width: w,
            height: h,
            attach(id) {
                gl.activeTexture(gl.TEXTURE0 + id);
                gl.bindTexture(gl.TEXTURE_2D, texture);
                return id;
            },
        };
    }

    function createDoubleFBO(w, h, internalFormat, format, type, filter) {
        let fbo1 = createFBO(w, h, internalFormat, format, type, filter);
        let fbo2 = createFBO(w, h, internalFormat, format, type, filter);
        return {
            width: w,
            height: h,
            texelSizeX: 1 / w,
            texelSizeY: 1 / h,
            get read() { return fbo1; },
            get write() { return fbo2; },
            swap() {
                const temp = fbo1;
                fbo1 = fbo2;
                fbo2 = temp;
            },
        };
    }

    function blit(target) {
        if (!target) {
            gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
            gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        } else {
            gl.viewport(0, 0, target.width, target.height);
            gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo);
        }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }

    const gl = canvas.getContext('webgl', {
        alpha: true,
        depth: false,
        stencil: false,
        antialias: false,
        preserveDrawingBuffer: false,
    });

    if (!gl) return;

    const extFloat = gl.getExtension('OES_texture_float');
    const extFloatLinear = gl.getExtension('OES_texture_float_linear');
    const extHalfFloat = gl.getExtension('OES_texture_half_float');
    const extHalfFloatLinear = gl.getExtension('OES_texture_half_float_linear');

    let textureType = null;
    let filtering = gl.NEAREST;

    if (extFloat) {
        textureType = gl.FLOAT;
        if (extFloatLinear) filtering = gl.LINEAR;
    } else if (extHalfFloat) {
        textureType = extHalfFloat.HALF_FLOAT_OES;
        if (extHalfFloatLinear) filtering = gl.LINEAR;
    }

    if (!textureType) return;

    gl.clearColor(0, 0, 0, 0);

    const programs = {
        copy: createProgram(baseVertexShader, copyShader),
        clear: createProgram(baseVertexShader, clearShader),
        display: createProgram(baseVertexShader, displayShader),
        splat: createProgram(baseVertexShader, splatShader),
        advection: createProgram(baseVertexShader, advectionShader),
        divergence: createProgram(baseVertexShader, divergenceShader),
        curl: createProgram(baseVertexShader, curlShader),
        vorticity: createProgram(baseVertexShader, vorticityShader),
        pressure: createProgram(baseVertexShader, pressureShader),
        gradientSubtract: createProgram(baseVertexShader, gradientSubtractShader),
    };

    const uniforms = {};
    Object.keys(programs).forEach((key) => {
        uniforms[key] = getUniforms(programs[key]);
    });

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, -1, 1, 1, 1, 1, -1]), gl.STATIC_DRAW);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(0);

    let dye;
    let velocity;
    let divergence;
    let curl;
    let pressure;
    let colorPhase = 0;
    let paletteIndex = 0;
    let lastMoveTime = 0;

    const pointers = [];
    const splatStack = [];

    function getResolution(resolution) {
        const aspect = canvas.clientWidth / Math.max(canvas.clientHeight, 1);
        let w = resolution;
        let h = resolution;
        if (aspect > 1) h = Math.round(resolution / aspect);
        else w = Math.round(resolution * aspect);
        return { width: w, height: h };
    }

    function initFramebuffers() {
        const simRes = getResolution(config.SIM_RESOLUTION);
        const dyeRes = getResolution(config.DYE_RESOLUTION);

        const texType = textureType;
        const rgba = gl.RGBA;
        const rg = gl.RGBA;

        velocity = createDoubleFBO(simRes.width, simRes.height, rgba, rgba, texType, filtering);
        divergence = createFBO(simRes.width, simRes.height, rgba, rgba, texType, gl.NEAREST);
        curl = createFBO(simRes.width, simRes.height, rgba, rgba, texType, gl.NEAREST);
        pressure = createDoubleFBO(simRes.width, simRes.height, rgba, rgba, texType, gl.NEAREST);
        dye = createDoubleFBO(dyeRes.width, dyeRes.height, rgba, rgba, texType, filtering);
    }

    function nextInkColor() {
        colorPhase += 1 / config.COLOR_UPDATE_SPEED;
        const i = paletteIndex % INK_PALETTE.length;
        const j = (i + 1) % INK_PALETTE.length;
        const t = colorPhase % 1;
        const c0 = INK_PALETTE[i];
        const c1 = INK_PALETTE[j];
        if (t < 0.02) paletteIndex += 1;
        return [
            c0[0] + (c1[0] - c0[0]) * t,
            c0[1] + (c1[1] - c0[1]) * t,
            c0[2] + (c1[2] - c0[2]) * t,
        ];
    }

    function splat(x, y, dx, dy, color) {
        splatStack.push({
            x,
            y,
            dx,
            dy,
            color: color || nextInkColor(),
        });
    }

    function applySplat({ x, y, dx, dy, color }) {
        gl.useProgram(programs.splat);
        gl.uniform1i(uniforms.splat.uTarget, velocity.read.attach(0));
        gl.uniform1f(uniforms.splat.aspectRatio, canvas.clientWidth / Math.max(canvas.clientHeight, 1));
        gl.uniform2f(uniforms.splat.point, x, y);
        gl.uniform3f(uniforms.splat.color, dx, dy, 0);
        gl.uniform1f(uniforms.splat.radius, config.SPLAT_RADIUS / 100);
        blit(velocity.write);
        velocity.swap();

        gl.uniform1i(uniforms.splat.uTarget, dye.read.attach(0));
        gl.uniform3f(uniforms.splat.color, color[0], color[1], color[2]);
        gl.uniform1f(uniforms.splat.radius, config.SPLAT_RADIUS / 80);
        blit(dye.write);
        dye.swap();
    }

    function step(dt) {
        gl.disable(gl.BLEND);

        gl.useProgram(programs.curl);
        gl.uniform2f(uniforms.curl.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.curl.uVelocity, velocity.read.attach(0));
        blit(curl);

        gl.useProgram(programs.vorticity);
        gl.uniform2f(uniforms.vorticity.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.vorticity.uVelocity, velocity.read.attach(0));
        gl.uniform1i(uniforms.vorticity.uCurl, curl.attach(1));
        gl.uniform1f(uniforms.vorticity.curl, config.CURL);
        gl.uniform1f(uniforms.vorticity.dt, dt);
        blit(velocity.write);
        velocity.swap();

        gl.useProgram(programs.divergence);
        gl.uniform2f(uniforms.divergence.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.divergence.uVelocity, velocity.read.attach(0));
        blit(divergence);

        gl.useProgram(programs.clear);
        gl.uniform1i(uniforms.clear.uTexture, pressure.read.attach(0));
        gl.uniform1f(uniforms.clear.value, config.PRESSURE);
        blit(pressure.write);
        pressure.swap();

        gl.useProgram(programs.pressure);
        gl.uniform2f(uniforms.pressure.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.pressure.uDivergence, divergence.attach(0));
        for (let i = 0; i < config.PRESSURE_ITERATIONS; i += 1) {
            gl.uniform1i(uniforms.pressure.uPressure, pressure.read.attach(1));
            blit(pressure.write);
            pressure.swap();
        }

        gl.useProgram(programs.gradientSubtract);
        gl.uniform2f(uniforms.gradientSubtract.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.gradientSubtract.uPressure, pressure.read.attach(0));
        gl.uniform1i(uniforms.gradientSubtract.uVelocity, velocity.read.attach(1));
        blit(velocity.write);
        velocity.swap();

        gl.useProgram(programs.advection);
        gl.uniform2f(uniforms.advection.texelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform2f(uniforms.advection.dyeTexelSize, velocity.texelSizeX, velocity.texelSizeY);
        gl.uniform1i(uniforms.advection.uVelocity, velocity.read.attach(0));
        gl.uniform1i(uniforms.advection.uSource, velocity.read.attach(0));
        gl.uniform1f(uniforms.advection.dt, dt);
        gl.uniform1f(uniforms.advection.dissipation, config.VELOCITY_DISSIPATION);
        blit(velocity.write);
        velocity.swap();

        gl.uniform2f(uniforms.advection.dyeTexelSize, dye.texelSizeX, dye.texelSizeY);
        gl.uniform1i(uniforms.advection.uVelocity, velocity.read.attach(0));
        gl.uniform1i(uniforms.advection.uSource, dye.read.attach(1));
        gl.uniform1f(uniforms.advection.dissipation, config.DENSITY_DISSIPATION);
        blit(dye.write);
        dye.swap();
    }

    function render() {
        gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        gl.enable(gl.BLEND);
        gl.useProgram(programs.display);
        gl.uniform1i(uniforms.display.uTexture, dye.read.attach(0));
        blit(null);
    }

    function resizeCanvas() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = window.innerWidth;
        const h = window.innerHeight;
        canvas.width = Math.floor(w * dpr);
        canvas.height = Math.floor(h * dpr);
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';
        initFramebuffers();
    }

    function updatePointer(id, x, y) {
        let p = pointers.find((item) => item.id === id);
        if (!p) {
            p = { id, x, y, px: x, py: y, moved: false };
            pointers.push(p);
        }
        p.px = p.x;
        p.py = p.y;
        p.x = x;
        p.y = y;
        p.moved = true;
    }

    function onPointerMove(e) {
        if (e.pointerType === 'touch') return;
        updatePointer(e.pointerId, e.clientX, e.clientY);
    }

    function onPointerDown(e) {
        if (e.pointerType === 'touch') return;
        updatePointer(e.pointerId, e.clientX, e.clientY);
    }

    function onPointerUp(e) {
        const idx = pointers.findIndex((p) => p.id === e.pointerId);
        if (idx >= 0) pointers.splice(idx, 1);
    }

    let lastFrame = performance.now();

    function frame(now) {
        const dt = Math.min((now - lastFrame) / 1000, 0.016);
        lastFrame = now;

        pointers.forEach((p) => {
            if (!p.moved) return;
            const nx = p.x / canvas.clientWidth;
            const ny = 1 - p.y / canvas.clientHeight;
            const dx = ((p.x - p.px) / canvas.clientWidth) * config.SPLAT_FORCE;
            const dy = (-(p.y - p.py) / canvas.clientHeight) * config.SPLAT_FORCE;
            if (Math.abs(dx) > 0.001 || Math.abs(dy) > 0.001 || now - lastMoveTime > 80) {
                splat(nx, ny, dx, dy);
                lastMoveTime = now;
            }
            p.moved = false;
        });

        while (splatStack.length) {
            applySplat(splatStack.pop());
        }

        step(dt);
        render();
        requestAnimationFrame(frame);
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas, { passive: true });
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('pointerdown', onPointerDown, { passive: true });
    window.addEventListener('pointerup', onPointerUp, { passive: true });
    window.addEventListener('pointercancel', onPointerUp, { passive: true });
    requestAnimationFrame(frame);
})();
