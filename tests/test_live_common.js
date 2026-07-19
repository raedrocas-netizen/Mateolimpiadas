const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");

const source = fs.readFileSync(
    path.join(__dirname, "..", "static", "js", "live_common.js"),
    "utf8"
);

function registeredSoundListeners(hasLiveView) {
    const listeners = [];
    const context = {
        Audio: class {},
        FormData: class {},
        document: {
            querySelector() {
                return hasLiveView ? {} : null;
            }
        },
        window: {
            addEventListener(eventName) {
                listeners.push(eventName);
            }
        }
    };

    vm.runInNewContext(source, context);
    return listeners;
}

test("does not preload competition audio from non-live pages", () => {
    assert.deepEqual(registeredSoundListeners(false), []);
});

test("keeps audio activation on live competition views", () => {
    assert.deepEqual(
        registeredSoundListeners(true),
        ["pointerdown", "keydown", "touchstart"]
    );
});
