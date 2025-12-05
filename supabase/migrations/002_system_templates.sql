-- Insert system templates for common product types

-- Inverter Generator Template
INSERT INTO product_templates (name, schema, is_system) VALUES (
  'Inverter Generator',
  '{
    "fields": [
      {
        "name": "price",
        "type": "decimal",
        "unit": "USD",
        "label": "Price",
        "compareDirection": "lower",
        "required": true
      },
      {
        "name": "wattage",
        "type": "integer",
        "unit": "W",
        "label": "Running Wattage",
        "compareDirection": "higher",
        "required": true
      },
      {
        "name": "weight",
        "type": "decimal",
        "unit": "lbs",
        "label": "Dry Weight",
        "compareDirection": "lower",
        "required": false
      },
      {
        "name": "dimensions",
        "type": "text",
        "label": "Dimensions",
        "compareDirection": "lower",
        "required": false
      }
    ],
    "metrics": [
      {
        "name": "dollar_per_wattage",
        "formula": "price / wattage",
        "label": "Dollar per Wattage",
        "compareDirection": "lower",
        "format": "currency"
      }
    ]
  }'::jsonb,
  true
);

