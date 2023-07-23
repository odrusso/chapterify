import {exec, spawn} from "child_process";
import {promisify} from "util";

export const execute = async (command: string, callback?: (stderr: string) => void) => {
    let p = spawn(command, {shell: true});

    return new Promise((resolveFunc) => {

        p.stdout.on("data", (x) => {
            if (callback) {
                callback(x.toString())
            }
        });

        p.stderr.on("data", (x) => {
            if (callback) {
                callback(x.toString())
            }
        });

        p.on("exit", (code) => {
            resolveFunc(code);
        });
    });
}

export const executeResult = promisify(exec)
