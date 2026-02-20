--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1.pgdg120+1)

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

ALTER TABLE IF EXISTS ONLY public.c_hos DROP CONSTRAINT IF EXISTS c_hos_pkey;
DROP TABLE IF EXISTS public.c_hos;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: c_hos; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.c_hos (
    hoscode character varying(5) NOT NULL,
    hosname character varying(255) NOT NULL,
    hostype character varying(50),
    hossize character varying(50),
    beds integer,
    hosname_short character varying(255),
    amp_code character varying(4),
    size_level character varying(10),
    gps character varying(50),
    sap_level character varying(20)
);


ALTER TABLE public.c_hos OWNER TO admin;

--
-- Data for Name: c_hos; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.c_hos (hoscode, hosname, hostype, hossize, beds, hosname_short, amp_code, size_level, gps, sap_level) FROM stdin;
10676	โรงพยาบาลพุทธชินราช	\N	\N	1020	รพ.พุทธชินราช	6501	A	16.8057098,100.2636709	P+
11251	โรงพยาบาลชาติตระการ	\N	\N	60	รพ.ชาติตระการ	6503	F1	17.2730857,100.6024606	S
11252	โรงพยาบาลบางระกำ	\N	\N	69	รพ.บางระกำ	6504	F1	16.7599303,100.1189124	S+
11253	โรงพยาบาลบางกระทุ่ม	\N	\N	30	รพ.บางกระทุ่ม	6505	F2	16.5753598,100.3180677	S
11254	โรงพยาบาลพรหมพิราม	\N	\N	50	รพ.พรหมพิราม	6506	F2	17.0348745,100.2010900	S+
11255	โรงพยาบาลวัดโบสถ์	\N	\N	30	รพ.วัดโบสถ์	6507	F2	16.9886108,100.3280342	S
11256	โรงพยาบาลวังทอง	\N	\N	68	รพ.วังทอง	6508	F1	16.8392002,100.4343728	S+
11257	โรงพยาบาลเนินมะปราง	\N	\N	39	รพ.เนินมะปราง	6509	F2	16.5603991,100.6251199	S
11455	โรงพยาบาลสมเด็จพระยุพราชนครไทย	\N	\N	120	รพ.นครไทย	6502	M2	17.0931910,100.8292097	S+
\.


--
-- Name: c_hos c_hos_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.c_hos
    ADD CONSTRAINT c_hos_pkey PRIMARY KEY (hoscode);


--
-- PostgreSQL database dump complete
--

