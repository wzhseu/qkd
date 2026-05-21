#ifndef _MESSAGE_HPP_
#define _MESSAGE_HPP_

#include <string>
#include <vector>
#include <unordered_map>
#include <boost/optional.hpp>

// The zmq server accepts JSON messages.
// message = {
//   "id"      : <the id of this message : Number>
//   "type"    : <the type of this message : String>
//   "payload" : <the payload of this message : Array(kv-pairs)>
// }
// kv-pairs = {
//   "key" : <key : String>,
//   "val" : <val : String>,
// }
#define MSG_ID          "id"
#define MSG_TYPE        "type"
#define MSG_PAYLOAD     "payload"
#define MSG_PAYLOAD_KEY "key"
#define MSG_PAYLOAD_VAL "val"

typedef enum {
  MT_GUARD_LO = 0,
  // Invalid message.
  MT_INVALID,
  MT_PING,
  // Get or set USRP configuration.
  MT_CONF,
  // Let USRP do some work.
  MT_WORK,
  MT_GUARD_HI,
} message_type;

// The payload is an array of key-value pairs.
using message_payload = std::vector<std::pair<std::string, std::string>>;

class message {
private:
  uint64_t id;
  message_type type;
  message_payload payload;

  mutable bool cached = false;
  mutable std::unordered_map<std::string, std::string> payload_cache;
public:
  // Disable default message ctor.
  message() = delete;
  message(uint64_t id, message_type type, message_payload payload);
  uint64_t get_id() const;
  message_type get_type() const;
  message_payload get_payload() const;
  std::unordered_map<std::string, std::string> &get_payload_as_map() const;

  static message from_json(std::string &json);
  static std::string to_json(message &msg);
};

#endif
