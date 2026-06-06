# ðŸŒ€ M.A.I Climate â€” HACS Integration

Quáº£n lÃ½ quáº¡t thÃ´ng minh trong Home Assistant: háº¹n giá», chá»‰ sá»‘ oi bá»©c, tá»± Ä‘á»™ng báº­t, giáº£i nhiá»‡t váº­n Ä‘á»™ng. Há»— trá»£ **nhiá»u quáº¡t Ä‘á»™c láº­p** â€” má»—i quáº¡t má»™t láº§n cÃ i Ä‘áº·t qua UI.

---

## TÃ­nh nÄƒng

| TÃ­nh nÄƒng | MÃ´ táº£ |
|-----------|-------|
| ðŸŒ¡ï¸ Chá»‰ sá»‘ oi bá»©c | TÃ­nh Heat Index tá»« nhiá»‡t Ä‘á»™ + Ä‘á»™ áº©m, hiá»ƒn thá»‹ qua sensor |
| â±ï¸ Háº¹n giá» thÃ´ng minh | Preset 15/30/45/60/90/120 phÃºt, chá»n qua UI dropdown |
| ðŸ”„ Auto-on | Tá»± báº­t quáº¡t khi chá»‰ sá»‘ oi bá»©c vÆ°á»£t ngÆ°á»¡ng tÃ¹y chá»‰nh |
| ðŸƒ Giáº£i nhiá»‡t váº­n Ä‘á»™ng | Báº­t quáº¡t 30 phÃºt sau khi táº­p thá»ƒ dá»¥c, tá»± táº¯t |
| ðŸ“± Bubble Card | Template card sáºµn sÃ ng dÃ¹ng vá»›i Bubble Card |
| ðŸ” NhÃ¢n rá»™ng | ThÃªm bao nhiÃªu quáº¡t cÅ©ng Ä‘Æ°á»£c, khÃ´ng cáº§n viáº¿t code |

---

## CÃ i Ä‘áº·t qua HACS

### BÆ°á»›c 1: ThÃªm repository vÃ o HACS

1. Má»Ÿ HACS â†’ **Integrations** â†’ dáº¥u **â‹®** â†’ **Custom repositories**
2. Nháº­p URL: `https://github.com/manhvuarchitect/M.A.I-Climate`
3. Category: **Integration** â†’ **Add**

### BÆ°á»›c 2: CÃ i Ä‘áº·t integration

1. TÃ¬m **M.A.I Climate** trong HACS â†’ **Download**
2. Khá»Ÿi Ä‘á»™ng láº¡i Home Assistant

### BÆ°á»›c 3: ThÃªm quáº¡t Ä‘áº§u tiÃªn

1. **Settings** â†’ **Devices & Services** â†’ **Add Integration**
2. TÃ¬m **M.A.I Climate**
3. Äiá»n thÃ´ng tin:
   - **TÃªn quáº¡t**: Quáº¡t phÃ²ng lÃ m viá»‡c
   - **Entity quáº¡t**: `fan.modul_homelab_switch_3`
   - **Cáº£m biáº¿n nhiá»‡t Ä‘á»™**: `sensor.nhiet_do_phong`
   - **Cáº£m biáº¿n Ä‘á»™ áº©m**: `sensor.do_am_phong` *(tÃ¹y chá»n)*
   - **NgÆ°á»¡ng tá»± Ä‘á»™ng báº­t**: `38` (Heat Index Â°C)

### BÆ°á»›c 4: ThÃªm quáº¡t tiáº¿p theo

Láº·p láº¡i BÆ°á»›c 3 cho má»—i quáº¡t má»›i â€” má»—i quáº¡t sáº½ cÃ³ bá»™ entity riÃªng.

---

## Entities Ä‘Æ°á»£c táº¡o tá»± Ä‘á»™ng

Vá»›i má»—i quáº¡t, integration tá»± táº¡o 4 entity:

```
sensor.tÃªn_quáº¡t_chá»‰_sá»‘_oi_bá»©c          # Heat Index hiá»‡n táº¡i (Â°C)
sensor.tÃªn_quáº¡t_timer_cÃ²n_láº¡i           # GiÃ¢y cÃ²n láº¡i cá»§a timer
switch.tÃªn_quáº¡t_giáº£i_nhiá»‡t_váº­n_Ä‘á»™ng     # Báº­t/táº¯t cháº¿ Ä‘á»™ 30 phÃºt
number.tÃªn_quáº¡t_ngÆ°á»¡ng_tá»±_Ä‘á»™ng_báº­t     # NgÆ°á»¡ng auto-on (25-60Â°C)
select.tÃªn_quáº¡t_háº¹n_giá»_táº¯t            # Chá»n preset timer
```

---

## Sá»­ dá»¥ng Bubble Card Template

1. Má»Ÿ file `blueprints/bubble_card_template.yaml`
2. Thay tháº¿ cÃ¡c placeholder:
   - `ENTRY_ID` â†’ entry_id thá»±c táº¿ *(Settings > Devices > M.A.I Climate > tÃªn quáº¡t > Entry ID)*
   - `FAN_ENTITY` â†’ entity quáº¡t, vÃ­ dá»¥ `fan.modul_homelab_switch_3`
   - `TÃŠN_QUáº T` â†’ prefix cá»§a entity, vÃ­ dá»¥ `quáº¡t_phÃ²ng_lÃ m_viá»‡c`

---

## Automation vÃ­ dá»¥

### Tá»± Ä‘á»™ng báº­t quáº¡t trÆ°á»›c giá» lÃ m viá»‡c

```yaml
automation:
  - alias: Báº­t quáº¡t trÆ°á»›c giá» lÃ m
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.quáº¡t_phÃ²ng_lÃ m_viá»‡c_chá»‰_sá»‘_oi_bá»©c
        above: 35
    action:
      - service: mai_climate.set_timer
        data:
          entry_id: !secret fan_workroom_entry_id
          minutes: 120
          mode: timer
```

### Giáº£i nhiá»‡t sau khi táº­p

```yaml
automation:
  - alias: Giáº£i nhiá»‡t sau workout
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
  entry_id: "abc123..."   # entry_id cá»§a quáº¡t
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
  minutes: 30             # chá»‰ dÃ¹ng khi mode: timer
```

---

## CÃ´ng thá»©c chá»‰ sá»‘ oi bá»©c

Heat Index (Steadman 1979) â€” pháº£n Ã¡nh cáº£m giÃ¡c nÃ³ng thá»±c táº¿ khi cÃ³ Ä‘á»™ áº©m:

```
HI = -8.78 + 1.61T + 2.34RH - 0.146TÃ—RH - 0.012TÂ² - 0.016RHÂ²
     + 0.00221TÂ²Ã—RH + 0.00072TÃ—RHÂ² - 0.000003583TÂ²Ã—RHÂ²
```

Náº¿u khÃ´ng cÃ³ cáº£m biáº¿n Ä‘á»™ áº©m, máº·c Ä‘á»‹nh RH = 70%.

| Chá»‰ sá»‘ | Má»©c Ä‘á»™ |
|--------|--------|
| < 30Â°C | Dá»… chá»‹u |
| 30â€“43Â°C | HÆ¡i oi |
| 43â€“48Â°C | Oi bá»©c |
| > 48Â°C | Ráº¥t oi bá»©c |

---

## ÄÃ³ng gÃ³p & BÃ¡o lá»—i

- Issues: https://github.com/manhvuarchitect/M.A.I-Climate/issues
- Discussions: https://github.com/manhvuarchitect/M.A.I-Climate/discussions

