-- Create my_products table
CREATE TABLE my_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku TEXT,
    name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    schema JSONB NOT NULL,
    data JSONB NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create competitor_listings table
CREATE TABLE competitor_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    my_product_id UUID NOT NULL REFERENCES my_products(id) ON DELETE CASCADE,
    url TEXT NOT NULL UNIQUE,
    retailer_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    data JSONB NOT NULL,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create price_history table
CREATE TABLE price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES competitor_listings(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create product_templates table
CREATE TABLE product_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    schema JSONB NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_my_products_user_id ON my_products(user_id);
CREATE INDEX idx_competitor_listings_user_id ON competitor_listings(user_id);
CREATE INDEX idx_competitor_listings_product_id ON competitor_listings(my_product_id);
CREATE INDEX idx_price_history_listing_id ON price_history(listing_id);
CREATE INDEX idx_price_history_recorded_at ON price_history(recorded_at);
CREATE INDEX idx_product_templates_user_id ON product_templates(user_id);
CREATE INDEX idx_product_templates_is_system ON product_templates(is_system);

-- Enable Row Level Security
ALTER TABLE my_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_templates ENABLE ROW LEVEL SECURITY;

-- RLS Policies for my_products
CREATE POLICY "Users can view their own products"
    ON my_products FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own products"
    ON my_products FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own products"
    ON my_products FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own products"
    ON my_products FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for competitor_listings
CREATE POLICY "Users can view their own competitor listings"
    ON competitor_listings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own competitor listings"
    ON competitor_listings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own competitor listings"
    ON competitor_listings FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own competitor listings"
    ON competitor_listings FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for price_history
CREATE POLICY "Users can view price history for their listings"
    ON price_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM competitor_listings
            WHERE competitor_listings.id = price_history.listing_id
            AND competitor_listings.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert price history for their listings"
    ON price_history FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM competitor_listings
            WHERE competitor_listings.id = price_history.listing_id
            AND competitor_listings.user_id = auth.uid()
        )
    );

-- RLS Policies for product_templates
CREATE POLICY "Users can view system templates and their own templates"
    ON product_templates FOR SELECT
    USING (is_system = TRUE OR auth.uid() = user_id);

CREATE POLICY "Users can insert their own templates"
    ON product_templates FOR INSERT
    WITH CHECK (auth.uid() = user_id OR is_system = TRUE);

CREATE POLICY "Users can update their own templates"
    ON product_templates FOR UPDATE
    USING (auth.uid() = user_id AND is_system = FALSE);

CREATE POLICY "Users can delete their own templates"
    ON product_templates FOR DELETE
    USING (auth.uid() = user_id AND is_system = FALSE);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update updated_at on my_products
CREATE TRIGGER update_my_products_updated_at
    BEFORE UPDATE ON my_products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

