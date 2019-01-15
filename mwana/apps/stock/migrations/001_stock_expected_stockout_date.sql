BEGIN;
ALTER TABLE stock_weeklystockmonitoringreport ADD COLUMN expected_stockout_date date;
COMMIT;
