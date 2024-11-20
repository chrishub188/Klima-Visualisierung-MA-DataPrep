-- Description: This script is used to build the database and load the data into the database

-- Turn on the timer to measure the time taken to execute the queries
.timer on

--Install the spatial extension first
INSTALL spatial;
LOAD spatial;

--Set the memory limit to 48GB to speed up queries when using disk db
--!!Check machine memory before setting memory limit!!
SET memory_limit='48GB';

--x,y,temperatur,messung,genauigkeit,ntzg,date

--Create the temp table
--pet,temp,latitude,longitude,ntzg,hour
CREATE TABLE temperature (
    x INTEGER,
    y INTEGER,
    temperatur FLOAT,
    messung FLOAT,
    genauigkeit FLOAT,
    ntzg SMALLINT,
    date DATETIME, 
);
COPY temperature FROM './csvdata/merged_data.csv';


CREATE TABLE stadtbezirke AS SELECT * FROM ST_Read('./geodata/epsg25832/statistische_bezirke_2020.geojson');

--Show table schema after creation
DESCRIBE temperature;
DESCRIBE stadtbezirke;

-- Select the Avg() temperature for each hour in each stadtteil and save it to a CSV file
-- Check Coordinate Reference System (CRS) mismatch!!
-- PET is just a random value for testing
COPY(SELECT 
    s.gid, 
    s.name, 
    t.date, 
    AVG(t.temperatur) AS avg_temp,
    MIN(t.temperatur) AS min_temp,
    MAX(t.temperatur) AS max_temp,
    AVG(t.temperatur+5) AS avg_pet,
    MIN(t.temperatur+5) AS min_pet,
    MAX(t.temperatur+5) AS max_pet
FROM stadtbezirke s
JOIN temperature t 
    ON ST_Contains(s.geom, ST_Point(t.x, t.y)) -- Spatial filter
    AND t.ntzg NOT IN (20,21,30,32)
GROUP BY s.gid, s.name, t.date 
ORDER BY s.gid, t.date) TO './aggregated/avg_temp_bezirke.csv' (HEADER, DELIMITER ',');

-- Without PET!!
-- COPY(SELECT 
--     s.gid, 
--     s.name, 
--     t.date, 
--     AVG(t.temperatur) AS avg_temp,
--     MIN(t.temperatur) AS min_temp,
--     MAX(t.temperatur) AS max_temp,
-- FROM stadtbezirke s
-- JOIN temperature t 
--     ON ST_Contains(s.geom, ST_Point(t.x, t.y)) -- Spatial filter
--     AND t.ntzg NOT IN (20,21,30,32)
-- GROUP BY s.gid, s.name, t.date 
-- ORDER BY s.gid, t.date) TO './testdata/aggregated/avg_temp_bezirke.csv' (HEADER, DELIMITER ',');



