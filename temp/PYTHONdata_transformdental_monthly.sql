--
-- PostgreSQL database dump
--

\restrict Hd2jnJUSgyte07bY3XMMOk0hHGvTgNF9u0MJj9hkHMOrClU4FRFe3TtvQFw7x14

-- Dumped from database version 17.7 (Debian 17.7-3.pgdg13+1)
-- Dumped by pg_dump version 17.7 (Debian 17.7-3.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: transform_sync_dental_monthly; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.transform_sync_dental_monthly (
    hoscode text NOT NULL,
    y integer NOT NULL,
    m integer NOT NULL,
    visit integer,
    d_update timestamp without time zone
);


ALTER TABLE public.transform_sync_dental_monthly OWNER TO admin;

--
-- Data for Name: transform_sync_dental_monthly; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.transform_sync_dental_monthly (hoscode, y, m, visit, d_update) FROM stdin;
11251	2025	1	1020	2026-02-24 14:56:28
11251	2025	6	830	2026-02-24 14:56:28
11253	2025	1	985	2026-02-24 14:56:28
11251	2025	11	1447	2026-02-24 14:56:28
11253	2025	3	1009	2026-02-24 14:56:28
11253	2025	6	1351	2026-02-24 14:56:28
11253	2025	8	1531	2026-02-24 14:56:28
11253	2025	11	1647	2026-02-24 14:56:28
11253	2026	1	1294	2026-02-24 14:56:28
11251	2025	2	1015	2026-02-24 14:56:28
11251	2025	7	1654	2026-02-24 14:56:28
11253	2025	2	934	2026-02-24 14:56:28
11251	2025	12	1227	2026-02-24 14:56:28
11253	2025	5	1147	2026-02-24 14:56:28
11253	2025	7	1928	2026-02-24 14:56:28
11253	2025	10	1786	2026-02-24 14:56:28
11253	2025	12	1560	2026-02-24 14:56:28
11251	2025	3	655	2026-02-24 14:56:28
11251	2025	8	689	2026-02-24 14:56:28
11251	2026	1	1036	2026-02-24 14:56:28
11253	2025	4	947	2026-02-24 14:56:28
11253	2025	9	1261	2026-02-24 14:56:28
11253	2026	2	558	2026-02-24 14:56:28
11251	2025	4	515	2026-02-24 14:56:28
11251	2025	9	740	2026-02-24 14:56:28
11251	2026	2	1156	2026-02-24 14:56:28
11251	2025	5	543	2026-02-24 14:56:28
11251	2025	10	1423	2026-02-24 14:56:28
\.


--
-- Name: transform_sync_dental_monthly transform_sync_dental_monthly_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.transform_sync_dental_monthly
    ADD CONSTRAINT transform_sync_dental_monthly_pkey PRIMARY KEY (hoscode, y, m);


--
-- PostgreSQL database dump complete
--

\unrestrict Hd2jnJUSgyte07bY3XMMOk0hHGvTgNF9u0MJj9hkHMOrClU4FRFe3TtvQFw7x14

