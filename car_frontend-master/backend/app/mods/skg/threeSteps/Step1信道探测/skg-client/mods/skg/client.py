import threading
import time
import json
import requests

from pathlib import Path
from flask import request
from mods.utils import STATUS_OK, failed_with_explain, get_param_or
from mods.skg.preprocessing.example import MyFirstPreprocessingMod as PPMod

class SKGClient:
    def __init__(self, usrp_servers, socketio, flask_app):
        self._usrp_servers = usrp_servers
        self._role = "self_txrx"
        self._usrp_server_addr = "127.0.0.1:5555"
        self._peer_server_addr = "127.0.0.1:5000"
        self._send_waveform_from = "/tmp/waveform.data"
        self._save_csi_to = "/tmp/csi/"
        self._save_waveform_to = "/tmp/wave/"
        self._save_generated_key_to = "/tmp/key/"
        self._key_agreement_proto_frequency = 1
        self._socketio = socketio

        ## Callbacks for running tasks, e.g., sample_from/to_file, shutdown_xxx_job.
        self._flask_app = flask_app
        self._flask_app.add_url_rule("/task", "task", self.run_task)

        ## self._thread_lock is protecting the self._running flag and the running thread.
        self._thread_lock = threading.Semaphore()
        ## self._running indicates whether the thread is running.
        self._running = False
        ## self._running_thread stores the running thread's instance.
        self._running_thread = None

    def get_role(self):
        return self._role

    def get_peer_server_addr(self):
        return "http://" + self._peer_server_addr

    def get_usrp_server_addr(self):
        return "tcp://" + self._usrp_server_addr

    def get_send_waveform_from(self):
        return self._send_waveform_from

    def get_save_csi_to(self):
        return self._save_csi_to

    def get_save_waveform_to(self):
        return self._save_waveform_to

    def get_save_generated_key_to(self):
        return self._save_generated_key_to

    def get_key_agreement_proto_frequency(self):
        return self._key_agreement_proto_frequency

    def update_config(self, config):
        with self._thread_lock:
            if self._running:
                return "There's a running thread, please stop it first", False
        self._role = config["role"]
        self._peer_server_addr = config["peer_server_addr"]
        self._usrp_server_addr = config["usrp_server_addr"]
        self._send_waveform_from = config["send_waveform_from"]
        self._save_csi_to = config["save_csi_to"]
        self._save_waveform_to = config["save_waveform_to"]
        self._save_generated_key_to = config["save_generated_key_to"]
        self._key_agreement_proto_frequency = \
            int(config["key_agreement_proto_frequency"], 10)
        return "", True

    def get_config(self):
        return {
            "role": self._role,
            "peer_server_addr": self._peer_server_addr,
            "usrp_server_addr": self._usrp_server_addr,
            "send_waveform_from": self._send_waveform_from,
            "save_csi_to": self._save_csi_to,
            "save_waveform_to": self._save_waveform_to,
            "save_generated_key_to": self._save_generated_key_to,
            "key_agreement_proto_frequency": self._key_agreement_proto_frequency,
        }

    def run_as_self_tx_rx(self):
        loop_cnt = 0
        pp = PPMod(self.get_send_waveform_from())
        while True:
            ## This thread won't modify self._running, so we don't
            ## need to lock it.
            if not self._running:
                break
            print("tx_thread running")

            ## Starting to sample to file.
            usrp_server_addr = self.get_usrp_server_addr()
            save_waveform_to = self.get_save_waveform_to() + "waveform_{}.data".format(loop_cnt)
            err_msg, ok = self._usrp_servers.sample_to_file(usrp_server_addr,
                                                      save_waveform_to)
            if not ok:
                print(err_msg)
                break

            ## RX Settling time.
            time.sleep(0.04)

            ## Start to send waveform.
            send_waveform_from = self.get_send_waveform_from()
            err_msg, ok = self._usrp_servers.sample_from_file(usrp_server_addr,
                                                              send_waveform_from)
            if not ok:
                print(err_msg)
                break

            ## Shutdown sample to file.
            self._usrp_servers.shutdown_sample_to_file(self.get_usrp_server_addr())

            ## Preprocessing.
            csi = pp.process(save_waveform_to)
            self._socketio.emit("csi", csi)
            ## Increase the loop count.
            loop_cnt += 1

    def run_as_alice(self):
        loop_cnt = 0
        while True:
            ## This thread won't modify self._running, so we don't
            ## need to lock it.
            if not self._running:
                break
            bob_server = self.get_peer_server_addr()
            payload = {
                "task": "sample_to_file",
                "interaction_index": str(loop_cnt)
            }
            resp = requests.get(bob_server + "/task", params=payload)
            resp = json.loads(resp.text)
            if resp["status"] != "ok":
                print("err0")
                continue

            time.sleep(0.02)
            ## Start to send waveform.
            usrp_server_addr = self.get_usrp_server_addr()
            send_waveform_from = self.get_send_waveform_from()
            err_msg, ok = self._usrp_servers.sample_from_file(usrp_server_addr,
                                                              send_waveform_from)
            if not ok:
                print(err_msg)
                continue

            payload = {
                "task": "shutdown_sample_to_file",
                "interaction_index": str(loop_cnt),
            }
            resp = requests.get(bob_server + "/task", params=payload)
            resp = json.loads(resp.text)
            if resp["status"] != "ok":
                print("err1")
                continue

            save_waveform_to = self.get_save_waveform_to() + "waveform_{}.data".format(loop_cnt)
            err_msg, ok = self._usrp_servers.sample_to_file(usrp_server_addr,
                                                            save_waveform_to)
            if not ok:
                print(err_msg)
                continue

            payload = {
                "task": "sample_from_file",
                "interaction_index": str(loop_cnt),
            }
            time.sleep(0.02)
            resp = requests.get(bob_server + "/task", params=payload)
            resp = json.loads(resp.text)

            self._usrp_servers.shutdown_sample_to_file(usrp_server_addr)
            if resp["status"] != "ok":
                print("err2")
                continue

            payload = {
                "task": "done",
                "interaction_index": str(loop_cnt),
            }
            resp = requests.get(bob_server + "/task", params=payload)
            resp = json.loads(resp.text)
            if resp["status"] != "ok":
                print("err3")
                continue
            pp = PPMod(self.get_send_waveform_from())
            save_waveform_to = self.get_save_waveform_to() + "waveform_{}.data".format(loop_cnt)
            csi = pp.process(save_waveform_to)
            self._socketio.emit("csi", csi)
            loop_cnt += 1

    def run_as_bob(self):
        pass

    def run_as_eve(self):
        pass

    def run(self):
        with self._thread_lock:
            if self._role == "select":
                return failed_with_explain("Please specify the role first")
            if self._running:
                return failed_with_explain("Currently, there's a job running. Please stop it first")
            self._running = True
            ## Check the existence of the directory.
            ## See: https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory-in-python
            Path(self.get_save_waveform_to()).mkdir(parents=True, exist_ok=True)
            Path(self.get_save_csi_to()).mkdir(parents=True, exist_ok=True)
            if self._role == "self_txrx":
                self._running_thread = threading.Thread(target=self.run_as_self_tx_rx)
            elif self._role == "alice":
                self._running_thread = threading.Thread(target=self.run_as_alice)
            self._running_thread.start()
            return STATUS_OK

    def stop(self):
        with self._thread_lock:
            if self._running:
                ## Stop the job
                self._running = False
                self._running_thread.join()
                self._running_thread = None
                return STATUS_OK
            return failed_with_explain("There's no job running")

    ## Callbacks.
    def run_task(self):
        with self._thread_lock:
            task = get_param_or(request, "task", "")
            if task == "":
                return failed_with_explain("Please specify the param: 'task'")
            interaction_index = int(get_param_or(request, "interaction_index", "-1"))
            if interaction_index == -1:
                return failed_with_explain("Please specify the param: 'interaction_index'")

            if task == "sample_to_file":
                ## Start to sample to file.
                usrp_server_addr = self.get_usrp_server_addr()
                save_waveform_to = self.get_save_waveform_to() + "waveform_{}.data".format(interaction_index)
                err_msg, ok = self._usrp_servers.sample_to_file(usrp_server_addr,
                                                                save_waveform_to)
                if not ok:
                    return failed_with_explain(err_msg)
                return STATUS_OK
            elif task == "sample_from_file":
                ## Start to send waveform.
                usrp_server_addr = self.get_usrp_server_addr()
                send_waveform_from = self.get_send_waveform_from()
                print(usrp_server_addr)
                print(send_waveform_from)
                err_msg, ok = self._usrp_servers.sample_from_file(usrp_server_addr,
                                                                  send_waveform_from)
                if not ok:
                    return failed_with_explain(err_msg)
                return STATUS_OK
            elif task == "shutdown_sample_to_file":
                self._usrp_servers.shutdown_sample_to_file(self.get_usrp_server_addr())
                return STATUS_OK
            elif task == "done":
                save_waveform_to = self.get_save_waveform_to()
                pp = PPMod(self.get_send_waveform_from())
                save_waveform_to = self.get_save_waveform_to() + "waveform_{}.data".format(interaction_index)
                csi = pp.process(save_waveform_to)
                if len(csi) == 0:
                    return STATUS_OK
                self._socketio.emit("csi", csi)
                return STATUS_OK
            return failed_with_explain("Unknown error")
