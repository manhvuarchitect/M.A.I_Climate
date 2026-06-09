import os

files = {
    'switch_ac.py': 'ac_name',
    'switch_purifier.py': 'purifier_name',
    'switch_vent.py': 'vent_name'
}

for fname, key_name in files.items():
    path = f'custom_components/mai_climate/{fname}'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from homeassistant.util import slugify' not in content:
        content = content.replace('from homeassistant.helpers.update_coordinator import CoordinatorEntity', 'from homeassistant.helpers.update_coordinator import CoordinatorEntity\nfrom homeassistant.util import slugify')

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        if 'self._attr_unique_id =' in line and 'self.entity_id =' not in lines[i+1]:
            # Extract suffix from unique_id
            parts = line.split('_attr_unique_id = f\"{entry.entry_id}_')
            if len(parts) == 2:
                suffix = parts[1].split('\"')[0] # e.g. ac_smart_sleep or purifier_auto_boost
                indent = line.split('self._attr_unique_id')[0]
                new_lines.append(f'{indent}slug_name = slugify(entry.data.get(\"{key_name}\", \"\")).replace(\"_\", \"\")')
                new_lines.append(f'{indent}self.entity_id = f\"switch.maic_{suffix}_{{slug_name}}\"')
        i += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print(f'Updated {fname}')
