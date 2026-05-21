#include <string>
#include <unordered_map>
#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>
#include "message.hpp"

namespace rj = rapidjson;
using mt = message_type;

static const char *get_str_or(const rj::Value &val, const char *fallback) {
  if (val.IsString())
    return val.GetString();
  return fallback;
}

static double get_double_or(const rj::Value &val, double fallback) {
  if (val.IsDouble())
    return val.GetDouble();
  return fallback;
}

static uint64_t get_uint64_or(const rj::Value &val, uint64_t fallback) {
  if (val.IsNumber())
    return val.GetUint64();
  return fallback;
}

static uint32_t get_uint32_or(const rj::Value &val, uint32_t fallback) {
  if (val.IsNumber())
    return val.GetUint();
  return fallback;
}

message::message(uint64_t id, mt type, message_payload payload)
  : id(id), type(type), payload(payload) {}

uint64_t message::get_id() const {
  return id;
}

mt message::get_type() const {
  return type;
}

message_payload message::get_payload() const {
  return payload;
}

std::unordered_map<std::string, std::string>&
message::get_payload_as_map() const {
  if (!cached) {
    for (auto& KV : payload)
      payload_cache.insert(KV);
    cached = true;
  }
  return payload_cache;
}

static uint64_t get_message_id(const rj::Value &val) {
  return get_uint64_or(val, 0);
}

static mt get_message_type(const rj::Value &val) {
  uint32_t type = get_uint32_or(val, mt::MT_INVALID);
  if (type <= mt::MT_GUARD_LO || type >= mt::MT_GUARD_HI)
    return mt::MT_INVALID;
  return static_cast<mt>(type);
}

static message_payload get_message_payload(const rj::Value &val) {
  message_payload payload;
  if (val.IsArray()) {
    for (rj::SizeType I = 0; I < val.Size(); ++I) {
      const rj::Value &k = val[I][MSG_PAYLOAD_KEY];
      const rj::Value &v = val[I][MSG_PAYLOAD_VAL];
      if (k.IsString() && v.IsString()) {
	payload.push_back({std::string(k.GetString()),
	    std::string(v.GetString())});
      }
    }
  }
  return payload;
}

static void create_message_id(rj::Value &obj, uint64_t id, rj::Document &d) {
  rj::Value v(rj::kNumberType);
  v.SetUint64(id);
  obj.AddMember(rj::StringRef(MSG_ID), v, d.GetAllocator());
}

static void create_message_type(rj::Value &obj, mt type, rj::Document &d) {
  rj::Value v(rj::kNumberType);
  v.SetUint(type);
  obj.AddMember(rj::StringRef(MSG_TYPE), v, d.GetAllocator());
}

static void create_message_payload(rj::Value &obj, message_payload &&payload,
				   rj::Document &d) {
  rj::Value v(rj::kArrayType);
  for (uint64_t I = 0; I < payload.size(); ++I) {
    std::string &key_str = payload[I].first;
    std::string &val_str = payload[I].second;
    rj::Value kv(rj::kObjectType);

    rj::Value key(rj::kStringType), val(rj::kStringType);
    // Make deep copy.
    key.SetString(key_str.c_str(), key_str.size(), d.GetAllocator());
    val.SetString(val_str.c_str(), val_str.size(), d.GetAllocator());
    kv.AddMember(rj::StringRef(MSG_PAYLOAD_KEY), key, d.GetAllocator());
    kv.AddMember(rj::StringRef(MSG_PAYLOAD_VAL), val, d.GetAllocator());

    v.PushBack(kv, d.GetAllocator());
  }
  obj.AddMember(rj::StringRef(MSG_PAYLOAD), v, d.GetAllocator());
}

message message::from_json(std::string &json) {
  rj::Document d;
  d.Parse(json.c_str());

  uint64_t id = get_message_id(d[MSG_ID]);
  mt type = get_message_type(d[MSG_TYPE]);
  message_payload payload = get_message_payload(d[MSG_PAYLOAD]);

  return message{id, type, payload};
}

std::string message::to_json(message &msg) {
  rj::Document d;
  rj::Value msg_obj(rj::kObjectType);
  // msg_obj = {
  //   "id"      : id      :: uint64,
  //   "type"    : type    :: uint32,
  //   "payload" : payload :: vector<pair<string, string>>,
  // }
  create_message_id(msg_obj, msg.get_id(), d);
  create_message_type(msg_obj, msg.get_type(), d);
  create_message_payload(msg_obj, msg.get_payload(), d);

  rj::StringBuffer buffer;
  rj::Writer<rj::StringBuffer> writer(buffer);
  msg_obj.Accept(writer);

  return std::string(buffer.GetString());
}
