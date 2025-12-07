# Unit Handling Design Considerations

## Current State

- **Schema**: Units are defined in `FieldDefinition.unit` (e.g., "USD", "W", "lbs", "gallons")
- **Data Storage**: Only numeric values are stored (e.g., `1.6`, not `"1.6 gallons"`)
- **AI Extraction**: AI is instructed to "convert units to match specified units" but no actual conversion happens
- **Comparisons**: Assumes values are already in the same unit (no conversion logic)
- **Display**: Units are shown in UI labels but not stored with data

## Design Options

### Option 1: Store Units with Data (Current + Enhancement)

**Approach**: Store both value and unit in data JSON
```json
{
  "fuel_tank_capacity": {
    "value": 1.6,
    "unit": "gallons"
  }
}
```

**Pros**:
- Preserves original unit information
- Can validate/extract units from web pages
- Allows unit conversion later
- More accurate data representation

**Cons**:
- More complex data structure
- Requires migration of existing data
- Comparisons need unit conversion logic
- More complex queries

**Implementation**:
- Update schema to support `{value, unit}` structure
- Add unit conversion library (e.g., `pint`)
- Update all comparison/calculation logic
- Migrate existing data

---

### Option 2: Convert During Extraction (Current Approach Enhanced)

**Approach**: AI converts units during extraction, store only normalized values

**Pros**:
- Simple data structure (just numbers)
- No conversion needed for comparisons
- Works with current codebase
- Fast comparisons

**Cons**:
- Relies on AI to do conversions correctly
- Loses original unit information
- Hard to debug if conversion is wrong
- AI might not know all unit conversions

**Implementation**:
- Enhance AI prompt with unit conversion instructions
- Add unit conversion examples to prompt
- Validate that extracted values are reasonable
- Log when conversions happen

---

### Option 3: Extract + Validate Units, Convert if Needed

**Approach**: Extract unit from web page, validate against schema, convert if different

**Pros**:
- Validates units match expectations
- Can detect extraction errors
- Still stores normalized values
- Better error handling

**Cons**:
- More complex extraction logic
- Need unit conversion library
- Need to parse units from text
- More edge cases to handle

**Implementation**:
- Extract unit from AI response or HTML
- Compare extracted unit to schema unit
- Convert if different (using conversion library)
- Store normalized value
- Log conversions for debugging

---

### Option 4: Hybrid - Store Units Separately

**Approach**: Store normalized value in `data`, store original unit in separate `units` field

```json
{
  "data": {
    "fuel_tank_capacity": 1.6
  },
  "units": {
    "fuel_tank_capacity": "gallons"
  }
}
```

**Pros**:
- Preserves original unit info
- Normalized values for easy comparison
- Can add units field without breaking existing code
- Best of both worlds

**Cons**:
- Two places to look for data
- Need to keep units in sync
- More complex data model

**Implementation**:
- Add optional `units` JSONB field to tables
- Extract and store units during crawling
- Use for display/validation, not comparisons
- Migrate gradually

---

## Recommended Approach: Option 3 (Extract + Validate + Convert)

### Why?
1. **Accuracy**: Validates that we're comparing apples to apples
2. **Debugging**: Can see what unit was extracted vs expected
3. **Flexibility**: Handles cases where web pages use different units
4. **Simplicity**: Still stores normalized values for comparisons

### Implementation Plan

1. **Unit Extraction**:
   - Extract unit from AI response (if provided)
   - Fallback: Parse from HTML/text content
   - Store extracted unit temporarily

2. **Unit Validation**:
   - Compare extracted unit to schema unit
   - Handle common variations (e.g., "gal" vs "gallons")
   - Warn/log if units don't match

3. **Unit Conversion**:
   - Use conversion library (e.g., `pint` or custom mappings)
   - Convert to schema unit if different
   - Store normalized numeric value

4. **Error Handling**:
   - If conversion fails, log warning
   - Store value as-is with warning flag
   - Allow manual correction

### Unit Conversion Library Options

**Option A: `pint` library**
```python
import pint
ureg = pint.UnitRegistry()
value = ureg.Quantity(1.6, "gallons").to("liters").magnitude
```
- Pros: Comprehensive, handles many units
- Cons: Additional dependency, might be overkill

**Option B: Custom conversion mappings**
```python
UNIT_CONVERSIONS = {
    ("gallons", "liters"): 3.78541,
    ("lbs", "kg"): 0.453592,
    # ... more mappings
}
```
- Pros: Lightweight, only what we need
- Cons: Need to maintain mappings, less flexible

**Option C: AI-assisted conversion**
- Ask AI to convert during extraction
- Pros: No library needed
- Cons: Less reliable, harder to debug

---

## Questions to Consider

1. **How important is unit accuracy?**
   - Critical for scientific products? → Option 1 or 3
   - Less critical for consumer products? → Option 2

2. **How often do units differ?**
   - Rarely? → Option 2 (current) is fine
   - Often? → Need Option 3 or 4

3. **Do we need historical unit info?**
   - Yes? → Option 1 or 4
   - No? → Option 2 or 3

4. **How complex are unit conversions?**
   - Simple (gallons→liters)? → Custom mappings
   - Complex (temperature, compound units)? → Need `pint`

5. **What's the priority?**
   - Speed of development? → Option 2 (enhance current)
   - Data accuracy? → Option 3
   - Future flexibility? → Option 1 or 4

---

## Next Steps

1. **Decide on approach** based on priorities
2. **Create unit conversion utility** (if needed)
3. **Update AI extractor** to handle units
4. **Add unit validation** to schema validator
5. **Update comparison logic** (if storing units)
6. **Add unit display** to frontend (if storing units)

