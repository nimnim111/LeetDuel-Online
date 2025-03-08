--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 14.17 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: problems; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.problems (
    problem_id integer NOT NULL,
    problem_name character varying(255) NOT NULL,
    problem_description text,
    test_cases jsonb,
    problem_difficulty character varying(50),
    function_signature text
);


ALTER TABLE public.problems OWNER TO admin;

--
-- Name: problems_problem_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.problems_problem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.problems_problem_id_seq OWNER TO admin;

--
-- Name: problems_problem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.problems_problem_id_seq OWNED BY public.problems.problem_id;


--
-- Name: problems problem_id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.problems ALTER COLUMN problem_id SET DEFAULT nextval('public.problems_problem_id_seq'::regclass);


--
-- Data for Name: problems; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.problems (problem_id, problem_name, problem_description, test_cases, problem_difficulty, function_signature) FROM stdin;
1	Two Sum	Given an array of integers, return indices of the two numbers such that they add up to a specific target	[{"input": "[[2, 7, 11, 15], 9]", "output": "[0, 1]"}, {"input": "[[3, 2, 4], 6]", "output": "[1, 2]"}, {"input": "[[3, 3], 6]", "output": "[0, 1]"}, {"input": "[[-1, 2, 4, 5], 3]", "output": "[0, 2]"}, {"input": "[[0, 5], 5]", "output": "[0, 1]"}, {"input": "[[-3, 3, 10], 0]", "output": "[0, 1]"}, {"input": "[[10, -10, 5], 0]", "output": "[0, 1]"}, {"input": "[[1, 9, 11, 12, 13], 10]", "output": "[0, 1]"}, {"input": "[[2, 5, 8, 9, 10], 7]", "output": "[0, 1]"}, {"input": "[[10, 20, 31, 35, 40], 30]", "output": "[0, 1]"}, {"input": "[[0, 5, 6, 7], 5]", "output": "[0, 1]"}, {"input": "[[100, 200, 301, 400], 300]", "output": "[0, 1]"}, {"input": "[[5, 5, 11, 12], 10]", "output": "[0, 1]"}, {"input": "[[1, 2, 4, 5, 6], 3]", "output": "[0, 1]"}, {"input": "[[-5, 7, 3, 4, 8], 2]", "output": "[0, 1]"}, {"input": "[[-10, 12], 2]", "output": "[0, 1]"}, {"input": "[[-8, 10], 2]", "output": "[0, 1]"}, {"input": "[[-1, 3], 2]", "output": "[0, 1]"}, {"input": "[[-7, 9], 2]", "output": "[0, 1]"}, {"input": "[[-5, 5, 6, 7], 0]", "output": "[0, 1]"}, {"input": "[[-3, 3, 4], 0]", "output": "[0, 1]"}, {"input": "[[0, 0], 0]", "output": "[0, 1]"}, {"input": "[[-1, 1, 2, 3], 0]", "output": "[0, 1]"}, {"input": "[[-100, 100, 200], 0]", "output": "[0, 1]"}, {"input": "[[-50, 50], 0]", "output": "[0, 1]"}, {"input": "[[0, 4], 4]", "output": "[0, 1]"}, {"input": "[[0, -5], -5]", "output": "[0, 1]"}, {"input": "[[0, 3, 7], 3]", "output": "[0, 1]"}, {"input": "[[0, 5, 10], 5]", "output": "[0, 1]"}, {"input": "[[1, -1], 0]", "output": "[0, 1]"}, {"input": "[[999, -999], 0]", "output": "[0, 1]"}, {"input": "[[-1000000, 1000000], 0]", "output": "[0, 1]"}, {"input": "[[2147483647, -2147483647], 0]", "output": "[0, 1]"}, {"input": "[[-1, 0], -1]", "output": "[0, 1]"}, {"input": "[[-2, -3], -5]", "output": "[0, 1]"}, {"input": "[[-10, -20], -30]", "output": "[0, 1]"}, {"input": "[[-7, 8], 1]", "output": "[0, 1]"}, {"input": "[[5, -3], 2]", "output": "[0, 1]"}, {"input": "[[100, -99], 1]", "output": "[0, 1]"}, {"input": "[[1, 99, 2, 3, 4], 100]", "output": "[0, 1]"}, {"input": "[[50, 50, 1, 2, 3], 100]", "output": "[0, 1]"}, {"input": "[[99, 1, 2, 3, 4], 100]", "output": "[0, 1]"}, {"input": "[[0, 100, 1, 2, 3], 100]", "output": "[0, 1]"}, {"input": "[[100, 0, 200, 300], 100]", "output": "[0, 1]"}, {"input": "[[-50, 150, 50, 60], 100]", "output": "[0, 1]"}, {"input": "[[10, 90, 22, 79], 100]", "output": "[0, 1]"}, {"input": "[[3, 2, 1], 5]", "output": "[0, 1]"}, {"input": "[[4, 5, 6, 7], 9]", "output": "[0, 1]"}, {"input": "[[10, 1, 2, 3], 11]", "output": "[0, 1]"}, {"input": "[[100, 200, 50, 150], 300]", "output": "[0, 1]"}, {"input": "[[-5, 10, 3], 5]", "output": "[0, 1]"}, {"input": "[[-10, 20, 5], 10]", "output": "[0, 1]"}, {"input": "[[0, 0], 0]", "output": "[0, 1]"}, {"input": "[[-1, -2, -3], -3]", "output": "[0, 1]"}, {"input": "[[5, -3, 8, 2], 2]", "output": "[0, 1]"}, {"input": "[[5, 4, 10, 11, 12], 9]", "output": "[0, 1]"}, {"input": "[[8, 1, 9, 10, 11], 9]", "output": "[0, 1]"}, {"input": "[[12, -3, 5, 6], 9]", "output": "[0, 1]"}, {"input": "[[100, -97, 50, 60], 3]", "output": "[0, 1]"}, {"input": "[[-50, 53, 10, 20], 3]", "output": "[0, 1]"}, {"input": "[[0, 7], 7]", "output": "[0, 1]"}, {"input": "[[7, 0], 7]", "output": "[0, 1]"}, {"input": "[[-5, 10, 4], 5]", "output": "[0, 1]"}, {"input": "[[2, -1, 5], 1]", "output": "[0, 1]"}, {"input": "[[-2, 3, 4], 1]", "output": "[0, 1]"}, {"input": "[[-10, 11, 5, 6], 1]", "output": "[0, 1]"}, {"input": "[[-7, 8, 3, 4], 1]", "output": "[0, 1]"}, {"input": "[[1000, -999, 500], 1]", "output": "[0, 1]"}, {"input": "[[-1, 2, 3, 4], 1]", "output": "[0, 1]"}, {"input": "[[5, 5, 10], 10]", "output": "[0, 1]"}, {"input": "[[-5, 15, 20], 10]", "output": "[0, 1]"}, {"input": "[[25, -15, 30], 10]", "output": "[0, 1]"}, {"input": "[[-20, 30, 40], 10]", "output": "[0, 1]"}, {"input": "[[0, 10], 10]", "output": "[0, 1]"}, {"input": "[[10, 0], 10]", "output": "[0, 1]"}, {"input": "[[7, 3], 10]", "output": "[0, 1]"}, {"input": "[[100, 200], 300]", "output": "[0, 1]"}, {"input": "[[-50, 150], 100]", "output": "[0, 1]"}, {"input": "[[123, -123], 0]", "output": "[0, 1]"}, {"input": "[[999999, 1], 1000000]", "output": "[0, 1]"}, {"input": "[[-2147483648, 2147483647], -1]", "output": "[0, 1]"}, {"input": "[[42, 17], 59]", "output": "[0, 1]"}, {"input": "[[17, 42], 59]", "output": "[0, 1]"}, {"input": "[[-3, 6], 3]", "output": "[0, 1]"}, {"input": "[[6, -3], 3]", "output": "[0, 1]"}, {"input": "[[0, 1000], 1000]", "output": "[0, 1]"}, {"input": "[[-1000, 0], -1000]", "output": "[0, 1]"}, {"input": "[[-10, 10], 0]", "output": "[0, 1]"}]	Easy	def run(nums: list[int], target: int) -> list[int]
2	Longest Substring Without Repeating Characters	Given a string s, find the length of the longest substring without duplicate characters.	[{"input": "[\\"abcabcbb\\"]", "output": "3"}]	Medium	def run(s: str) -> int
\.


--
-- Name: problems_problem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.problems_problem_id_seq', 2, true);


--
-- Name: problems problems_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_pkey PRIMARY KEY (problem_id);


--
-- PostgreSQL database dump complete
--

