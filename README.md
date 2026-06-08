# 🌀 M.A.I Climate — HACS Integration

Quản lý thiết bị khí hậu thông minh trong Home Assistant: hẹn giờ, chỉ số oi bức, tự động bật/tắt, giải nhiệt vận động. Hỗ trợ **quạt, điều hòa, máy lọc không khí, quạt thông gió** — mỗi thiết bị cài đặt độc lập chỉ với một lần cấu hình qua UI.

---

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 🌡️ Chỉ số oi bức | Tính Heat Index từ nhiệt độ + độ ẩm, hiển thị qua sensor |
| ⏱️ Hẹn giờ thông minh | Preset 15/30/45/60/90/120 phút, chọn qua UI dropdown |
| 🔄 Auto-on | Tự bật quạt khi chỉ số oi bức vượt ngưỡng tùy chỉnh |
| 🏃 Giải nhiệt vận động | Bật quạt 30 phút sau khi tập thể dục, tự tắt |
| 🎛️ Tốc độ thông minh | Tự thay đổi % tốc độ quạt theo độ oi bức (>40°C: 100%, <35°C: 33%) |
| 🌙 Chế độ ngủ | Tự động giảm tốc độ 10% mỗi giờ để tránh cảm lạnh ban đêm |
| 🍃 Gió tự nhiên | Tạo luồng gió ngẫu nhiên tốt cho sức khỏe |
| 🤫 Khung giờ yên tĩnh | Quạt chỉ bật mức thấp nhất trong thời gian ngủ |
| 📱 Custom Card | Có sẵn Lovelace card riêng biệt (`mai-climate-card`) cực đẹp |
| 🔁 Nhân rộng | Thêm bao nhiêu quạt cũng được, không cần viết code |

---

## Cài đặt qua HACS

### Bước 1: Thêm repository vào HACS

1. Mở HACS → **Integrations** → dấu **⋮** → **Custom repositories**
2. Nhập URL: `https://github.com/manhvuarchitect/M.A.I_Climate`
3. Category: **Integration** → **Add**

### Bước 2: Cài đặt integration

1. Tìm **M.A.I Climate** trong HACS → **Download**
2. Khởi động lại Home Assistant

### Bước 3: Thêm quạt đầu tiên

1. **Settings** → **Devices & Services** → **Add Integration**
2. Tìm **M.A.I Climate**
3. Điền thông tin:
   - **Tên quạt**: Quạt phòng làm việc
   - **Entity quạt**: `fan.modul_homelab_switch_3`
   - **Cảm biến nhiệt độ**: `sensor.nhiet_do_phong`
   - **Cảm biến độ ẩm**: `sensor.do_am_phong` *(tùy chọn)*
   - **Ngưỡng tự động bật**: `38` (Heat Index °C)

### Bước 4: Thêm quạt tiếp theo

Lặp lại Bước 3 cho mỗi quạt mới — mỗi quạt sẽ có bộ entity riêng.

---

## Entities được tạo tự động

Với mỗi quạt, integration tự tạo 4 entity:

```
sensor.tên_quạt_muggy_index            # Heat Index hiện tại (°C)
sensor.tên_quạt_timer_remaining        # Giây còn lại của timer
switch.tên_quạt_cooldown_mode          # Bật/tắt chế độ 30 phút
switch.tên_quạt_auto_on_mode           # Bật/tắt chế độ tự động bật
switch.tên_quạt_smart_speed_enabled    # Tốc độ thông minh (Auto Speed)
switch.tên_quạt_sleep_mode_enabled     # Chế độ ngủ (Sleep Mode)
switch.tên_quạt_natural_wind_enabled   # Gió tự nhiên (Natural Wind)
switch.tên_quạt_quiet_hours_enabled    # Khung giờ yên tĩnh (Quiet Hours)
number.tên_quạt_auto_on_threshold      # Ngưỡng auto-on (25-60°C)
select.tên_quạt_timer_preset           # Chọn preset timer
```

---

## 🎨 Hướng dẫn sử dụng Custom Card (`mai-climate-card`)

M.A.I Climate đi kèm một giao diện Custom Card tích hợp sẵn, không cần tải thêm qua HACS Frontend.

**Bước 1: Thêm Resource vào Lovelace**
1. Mở Home Assistant -> **Settings** -> **Dashboards**
2. Nhấn vào dấu **⋮** ở góc trên -> chọn **Resources**
3. Nhấn **Add Resource**
4. URL: `/mai_climate_card/mai-climate-card.js`
5. Resource Type: `JavaScript Module` -> Lưu lại.

**Bước 2: Thêm thẻ vào Dashboard**
1. Mở Dashboard -> **Edit Dashboard** -> **Add Card** -> **Manual**
2. Nhập code sau:
```yaml
type: custom:mai-climate-card
entity: fan.ten_quat_cua_ban
```

---

## Sử dụng Bubble Card Template

1. Mở file `blueprints/bubble_card_template.yaml`
2. Thay thế các placeholder:
   - `ENTRY_ID` → entry_id thực tế *(Settings > Devices > M.A.I Climate > tên quạt > Entry ID)*
   - `FAN_ENTITY` → entity quạt, ví dụ `fan.modul_homelab_switch_3`
   - `TÊN_QUẠT` → prefix của entity, ví dụ `quạt_phòng_làm_việc`

---

## Automation ví dụ

### Tự động bật quạt trước giờ làm việc

```yaml
automation:
  - alias: Bật quạt trước giờ làm
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.quạt_phòng_làm_việc_muggy_index
        above: 35
    action:
      - service: mai_climate.set_timer
        data:
          entry_id: !secret fan_workroom_entry_id
          minutes: 120
          mode: timer
```

### Giải nhiệt sau khi tập

```yaml
automation:
  - alias: Giải nhiệt sau workout
    trigger:
      - platform: state
        entity_id: input_boolean.dang_tap_the_duc
        to: "off"
    action:
      - service: mai_climate.set_mode
        data:
          entry_id: !secret fan_bedroom_entry_id
          mode: cooldown
```

---

## Services

### `mai_climate.set_timer`
```yaml
service: mai_climate.set_timer
data:
  entry_id: "abc123..."   # entry_id của quạt
  minutes: 45             # 1-480
  mode: timer             # timer | cooldown
```

### `mai_climate.cancel_timer`
```yaml
service: mai_climate.cancel_timer
data:
  entry_id: "abc123..."
```

### `mai_climate.set_mode`
```yaml
service: mai_climate.set_mode
data:
  entry_id: "abc123..."
  mode: cooldown          # cooldown | timer
  minutes: 30             # chỉ dùng khi mode: timer
```

---

## Công thức chỉ số oi bức

Heat Index (Steadman 1979) — phản ánh cảm giác nóng thực tế khi có độ ẩm:

```
HI = -8.78 + 1.61T + 2.34RH - 0.146T×RH - 0.012T² - 0.016RH²
     + 0.00221T²×RH + 0.00072T×RH² - 0.000003583T²×RH²
```

Nếu không có cảm biến độ ẩm, mặc định RH = 70%.

| Chỉ số | Mức độ |
|--------|--------|
| < 30°C | Dễ chịu |
| 30–43°C | Hơi oi |
| 43–48°C | Oi bức |
| > 48°C | Rất oi bức |

---

## Đóng góp & Báo lỗi

- Issues: https://github.com/manhvuarchitect/M.A.I_Climate/issues
- Discussions: https://github.com/manhvuarchitect/M.A.I_Climate/discussions
