--
-- PostgreSQL database dump
--

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.3

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

--
-- Name: _heroku; Type: SCHEMA; Schema: -; Owner: heroku_admin
--

CREATE SCHEMA _heroku;


ALTER SCHEMA _heroku OWNER TO heroku_admin;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: u15smncfh5gol7
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO u15smncfh5gol7;

--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: create_ext(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.create_ext() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

DECLARE

  schemaname TEXT;
  databaseowner TEXT;

  r RECORD;

BEGIN
  IF tg_tag OPERATOR(pg_catalog.=) 'CREATE EXTENSION' THEN
    PERFORM _heroku.validate_search_path();

    FOR r IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands()
    LOOP
        CONTINUE WHEN r.command_tag != 'CREATE EXTENSION' OR r.object_type != 'extension';

        schemaname := (
            SELECT n.nspname
            FROM pg_catalog.pg_extension AS e
            INNER JOIN pg_catalog.pg_namespace AS n
            ON e.extnamespace = n.oid
            WHERE e.oid = r.objid
        );

        databaseowner := (
            SELECT pg_catalog.pg_get_userbyid(d.datdba)
            FROM pg_catalog.pg_database d
            WHERE d.datname = pg_catalog.current_database()
        );
        --RAISE NOTICE 'Record for event trigger %, objid: %,tag: %, current_user: %, schema: %, database_owenr: %', r.object_identity, r.objid, tg_tag, current_user, schemaname, databaseowner;
        IF r.object_identity = 'address_standardizer_data_us' THEN
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'us_gaz');
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'us_lex');
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'us_rules');
        ELSIF r.object_identity = 'amcheck' THEN
            -- Grant execute permissions on amcheck functions (bt_*, gin_*, and verify_*)
            PERFORM _heroku.grant_function_execute_for_extension(r.objid, schemaname, databaseowner, ARRAY['bt_%', 'gin_%', 'verify_%'], NULL);
        ELSIF r.object_identity = 'dblink' THEN
            -- Grant execute permissions on dblink functions, excluding dblink_connect_u()
            -- which allows unauthenticated connections and should remain superuser-only
            PERFORM _heroku.grant_function_execute_for_extension(r.objid, schemaname, databaseowner, ARRAY['dblink%'], 'dblink_connect_u%');
            -- Explicitly revoke permissions on dblink_connect_u functions as a safety measure
            -- in case they were granted by default or in a previous version
            BEGIN
                EXECUTE pg_catalog.format('REVOKE EXECUTE ON FUNCTION %I.dblink_connect_u(text) FROM %I;', schemaname, databaseowner);
            EXCEPTION WHEN OTHERS THEN
                -- Function might not exist, continue
                NULL;
            END;
            BEGIN
                EXECUTE pg_catalog.format('REVOKE EXECUTE ON FUNCTION %I.dblink_connect_u(text, text) FROM %I;', schemaname, databaseowner);
            EXCEPTION WHEN OTHERS THEN
                -- Function might not exist, continue
                NULL;
            END;
        ELSIF r.object_identity = 'dict_int' THEN
            EXECUTE pg_catalog.format('ALTER TEXT SEARCH DICTIONARY %I.intdict OWNER TO %I;', schemaname, databaseowner);
        ELSIF r.object_identity = 'pg_prewarm' THEN
            -- Grant execute permissions on pg_prewarm and autoprewarm functions
            PERFORM _heroku.grant_function_execute_for_extension(
                r.objid, schemaname, databaseowner, ARRAY['pg_prewarm%', 'autoprewarm%'], NULL
            );
        ELSIF r.object_identity = 'pg_partman' THEN
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'part_config');
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'part_config_sub');
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT, UPDATE, INSERT, DELETE', databaseowner, 'custom_time_partitions');
        ELSIF r.object_identity = 'pg_stat_statements' THEN
            -- Grant execute permissions on pg_stat_statements functions
            PERFORM _heroku.grant_function_execute_for_extension(
                r.objid, schemaname, databaseowner, ARRAY['pg_stat_statements%'], NULL
            );
        ELSIF r.object_identity = 'postgres_fdw' THEN
            -- Grant USAGE on the foreign data wrapper (required for creating foreign servers and user mappings)
            EXECUTE pg_catalog.format('GRANT USAGE ON FOREIGN DATA WRAPPER postgres_fdw TO %I;', databaseowner);
            -- Grant execute permissions on all postgres_fdw functions
            PERFORM _heroku.grant_function_execute_for_extension(r.objid, schemaname, databaseowner, ARRAY['postgres_fdw%'], NULL);
        ELSIF r.object_identity = 'postgis' THEN
            PERFORM _heroku.postgis_after_create();
        ELSIF r.object_identity = 'postgis_raster' THEN
            PERFORM _heroku.postgis_after_create();
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT', databaseowner, 'raster_columns');
            PERFORM _heroku.grant_table_if_exists(schemaname, 'SELECT', databaseowner, 'raster_overviews');
        ELSIF r.object_identity = 'postgis_topology' THEN
            PERFORM _heroku.postgis_after_create();
            EXECUTE pg_catalog.format('ALTER SCHEMA topology OWNER TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT USAGE ON SCHEMA topology TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA topology TO %I;', databaseowner);
            PERFORM _heroku.grant_table_if_exists('topology', 'SELECT, UPDATE, INSERT, DELETE', databaseowner);
            EXECUTE pg_catalog.format('GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA topology TO %I;', databaseowner);
        ELSIF r.object_identity = 'postgis_tiger_geocoder' THEN
            PERFORM _heroku.postgis_after_create();
            EXECUTE pg_catalog.format('ALTER SCHEMA tiger OWNER TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT USAGE ON SCHEMA tiger TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA tiger TO %I;', databaseowner);
            PERFORM _heroku.grant_table_if_exists('tiger', 'SELECT, UPDATE, INSERT, DELETE', databaseowner);
            EXECUTE pg_catalog.format('ALTER SCHEMA tiger_data OWNER TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT USAGE ON SCHEMA tiger_data TO %I;', databaseowner);
            EXECUTE pg_catalog.format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA tiger_data TO %I;', databaseowner);
            PERFORM _heroku.grant_table_if_exists('tiger_data', 'SELECT, UPDATE, INSERT, DELETE', databaseowner);
        END IF;
    END LOOP;
  END IF;
END;
$$;


ALTER FUNCTION _heroku.create_ext() OWNER TO heroku_admin;

--
-- Name: drop_ext(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.drop_ext() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

DECLARE

  schemaname TEXT;
  databaseowner TEXT;

  r RECORD;

BEGIN
  IF tg_tag OPERATOR(pg_catalog.=) 'DROP EXTENSION' THEN
    PERFORM _heroku.validate_search_path();

    FOR r IN SELECT * FROM pg_catalog.pg_event_trigger_dropped_objects()
    LOOP
      CONTINUE WHEN r.object_type != 'extension';

      databaseowner := (
            SELECT pg_catalog.pg_get_userbyid(d.datdba)
            FROM pg_catalog.pg_database d
            WHERE d.datname = pg_catalog.current_database()
      );

      --RAISE NOTICE 'Record for event trigger %, objid: %,tag: %, current_user: %, database_owner: %, schemaname: %', r.object_identity, r.objid, tg_tag, current_user, databaseowner, r.schema_name;

      IF r.object_identity = 'postgis_topology' THEN
          EXECUTE pg_catalog.format('DROP SCHEMA IF EXISTS topology');
      END IF;
    END LOOP;

  END IF;
END;
$$;


ALTER FUNCTION _heroku.drop_ext() OWNER TO heroku_admin;

--
-- Name: extension_before_drop(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.extension_before_drop() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

DECLARE

  query TEXT;

BEGIN
  query := (SELECT pg_catalog.current_query());

  -- RAISE NOTICE 'executing extension_before_drop: tg_event: %, tg_tag: %, current_user: %, session_user: %, query: %', tg_event, tg_tag, current_user, session_user, query;
  -- skip this validation if executed by an rds_superuser
  IF tg_tag OPERATOR(pg_catalog.=) 'DROP EXTENSION' AND NOT pg_catalog.pg_has_role(session_user, 'rds_superuser', 'MEMBER') THEN
    PERFORM _heroku.validate_search_path();

    -- DROP EXTENSION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]
    IF (pg_catalog.regexp_match(query, 'DROP\s+EXTENSION\s+(IF\s+EXISTS)?.*(plpgsql)', 'i') IS NOT NULL) THEN
      RAISE EXCEPTION 'The plpgsql extension is required for database management and cannot be dropped.';
    END IF;
  END IF;
END;
$$;


ALTER FUNCTION _heroku.extension_before_drop() OWNER TO heroku_admin;

--
-- Name: grant_function_execute_for_extension(oid, text, text, text[], text); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.grant_function_execute_for_extension(extension_oid oid, schemaname text, databaseowner text, name_patterns text[] DEFAULT NULL::text[], exclude_pattern text DEFAULT NULL::text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

DECLARE
    func_rec RECORD;

BEGIN
    PERFORM _heroku.validate_search_path();

    -- Dynamically grant execute permissions on extension functions.
    -- Finds functions belonging to the extension via pg_depend and grants execute permissions.
    FOR func_rec IN
        SELECT p.oid::regprocedure::text as func_sig
        FROM pg_catalog.pg_depend d
        JOIN pg_catalog.pg_proc p ON d.objid = p.oid
        JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
        WHERE d.refclassid = 'pg_catalog.pg_extension'::regclass
          AND d.refobjid = extension_oid
          AND d.deptype = 'e'
          AND n.nspname = schemaname
          AND (name_patterns IS NULL OR p.proname LIKE ANY(name_patterns))
          AND (exclude_pattern IS NULL OR p.proname NOT LIKE exclude_pattern)
    LOOP
        BEGIN
            EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %s TO %I;', func_rec.func_sig, databaseowner);
        EXCEPTION WHEN OTHERS THEN
            -- Function might not exist or already granted, continue
            NULL;
        END;
    END LOOP;
END;
$$;


ALTER FUNCTION _heroku.grant_function_execute_for_extension(extension_oid oid, schemaname text, databaseowner text, name_patterns text[], exclude_pattern text) OWNER TO heroku_admin;

--
-- Name: grant_table_if_exists(text, text, text, text); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.grant_table_if_exists(alias_schemaname text, grants text, databaseowner text, alias_tablename text DEFAULT NULL::text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

BEGIN
  PERFORM _heroku.validate_search_path();

  IF alias_tablename IS NULL THEN
    EXECUTE pg_catalog.format('GRANT %s ON ALL TABLES IN SCHEMA %I TO %I;', grants, alias_schemaname, databaseowner);
  ELSE
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables WHERE pg_tables.schemaname = alias_schemaname AND pg_tables.tablename = alias_tablename) THEN
      EXECUTE pg_catalog.format('GRANT %s ON TABLE %I.%I TO %I;', grants, alias_schemaname, alias_tablename, databaseowner);
    END IF;
  END IF;
END;
$$;


ALTER FUNCTION _heroku.grant_table_if_exists(alias_schemaname text, grants text, databaseowner text, alias_tablename text) OWNER TO heroku_admin;

--
-- Name: postgis_after_create(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.postgis_after_create() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    schemaname TEXT;
    databaseowner TEXT;
BEGIN
    PERFORM _heroku.validate_search_path();

    schemaname := (
        SELECT n.nspname
        FROM pg_catalog.pg_extension AS e
        INNER JOIN pg_catalog.pg_namespace AS n ON e.extnamespace = n.oid
        WHERE e.extname = 'postgis'
    );
    databaseowner := (
        SELECT pg_catalog.pg_get_userbyid(d.datdba)
        FROM pg_catalog.pg_database d
        WHERE d.datname = pg_catalog.current_database()
    );

    EXECUTE pg_catalog.format('GRANT EXECUTE ON FUNCTION %I.st_tileenvelope TO %I;', schemaname, databaseowner);
    EXECUTE pg_catalog.format('GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE %I.spatial_ref_sys TO %I;', schemaname, databaseowner);
END;
$$;


ALTER FUNCTION _heroku.postgis_after_create() OWNER TO heroku_admin;

--
-- Name: sanitize_search_path(text); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.sanitize_search_path(unsafe_search_path text DEFAULT NULL::text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
  search_path_parts TEXT[];
  safe_search_path TEXT;
BEGIN
  IF unsafe_search_path IS NULL THEN
    unsafe_search_path := pg_catalog.current_setting('search_path');
  END IF;

  search_path_parts := pg_catalog.string_to_array(unsafe_search_path, ',');
  search_path_parts := (
    SELECT pg_catalog.array_agg(TRIM(schema_name::text))
    FROM pg_catalog.unnest(search_path_parts) AS schema_name
    WHERE TRIM(schema_name::text) OPERATOR(pg_catalog.!~~) 'pg_temp%'
  );
  search_path_parts := (SELECT pg_catalog.array_remove(search_path_parts, 'pg_catalog'));
  search_path_parts := (SELECT pg_catalog.array_append(search_path_parts, 'pg_temp'));
  SELECT pg_catalog.array_to_string(search_path_parts, ',') INTO safe_search_path;
  RETURN safe_search_path;
END;
$$;


ALTER FUNCTION _heroku.sanitize_search_path(unsafe_search_path text) OWNER TO heroku_admin;

--
-- Name: validate_extension(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.validate_extension() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$

DECLARE

  schemaname TEXT;
  r RECORD;

BEGIN
  IF tg_tag OPERATOR(pg_catalog.=) 'CREATE EXTENSION' THEN
    PERFORM _heroku.validate_search_path();

    FOR r IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands()
    LOOP
      CONTINUE WHEN r.command_tag != 'CREATE EXTENSION' OR r.object_type != 'extension';

      schemaname := (
        SELECT n.nspname
        FROM pg_catalog.pg_extension AS e
        INNER JOIN pg_catalog.pg_namespace AS n
        ON e.extnamespace = n.oid
        WHERE e.oid = r.objid
      );

      IF schemaname = '_heroku' THEN
        RAISE EXCEPTION 'Creating extensions in the _heroku schema is not allowed';
      END IF;
    END LOOP;
  END IF;
END;
$$;


ALTER FUNCTION _heroku.validate_extension() OWNER TO heroku_admin;

--
-- Name: validate_search_path(); Type: FUNCTION; Schema: _heroku; Owner: heroku_admin
--

CREATE FUNCTION _heroku.validate_search_path() RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE

  current_search_path TEXT;
  safe_search_path TEXT;
  current_schemas TEXT[];
  pg_catalog_index INTEGER;

BEGIN

  current_search_path := pg_catalog.current_setting('search_path');
  current_schemas := (SELECT pg_catalog.current_schemas(true));
  safe_search_path := _heroku.sanitize_search_path(current_search_path);

  IF current_schemas[1] OPERATOR(pg_catalog.~~) 'pg_temp%' THEN
    RAISE EXCEPTION 'Unable to perform this operation with current schema configuration. Try: SET search_path TO %.', safe_search_path;
  END IF;

  IF ('pg_catalog' OPERATOR(pg_catalog.=) ANY(current_schemas)) THEN
    SELECT pg_catalog.array_position(current_schemas, 'pg_catalog') INTO pg_catalog_index;
    IF pg_catalog_index OPERATOR(pg_catalog.!=) 1 THEN
      RAISE EXCEPTION 'Unable to perform this operation with current schema configuration. Try: SET search_path TO %.', safe_search_path;
    END IF;
  END IF;
END;
$$;


ALTER FUNCTION _heroku.validate_search_path() OWNER TO heroku_admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: feedback; Type: TABLE; Schema: public; Owner: u15smncfh5gol7
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    feedback_image character varying(255),
    correct_diagnosis character varying(255),
    diagnosis_correct boolean,
    predicted_classes character varying(255),
    clinical_case text,
    feedback_image_name character varying(255),
    feedback_image_url text,
    differential_diagnosis text
);


ALTER TABLE public.feedback OWNER TO u15smncfh5gol7;

--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: u15smncfh5gol7
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feedback_id_seq OWNER TO u15smncfh5gol7;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: u15smncfh5gol7
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: u15smncfh5gol7
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: u15smncfh5gol7
--

COPY public.feedback (id, feedback_image, correct_diagnosis, diagnosis_correct, predicted_classes, clinical_case, feedback_image_name, feedback_image_url, differential_diagnosis) FROM stdin;
1	uploads/1720417519691-cropped-image.png	Corpo Estranho	f	Otite Média Crônica - Simples: 61.8%, Otite Média Aguda - Bacteriana: 31.2%, Normal: 5.1%	Cerume e Cabelo	\N	\N	\N
2	\N	\N	t	Otite Externa Aguda - Difusa: 89.2%, Cerume Impactado: 6.9%, Pós Operatório: Timpanoplastia: 2.4%	Residuos de Gota Otológica. 	cropped-image.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720577368/qhvuaubrfhdodix2brpk.png	\N
3	\N	Otite Media Crônica Simples	f	Otite Média Serosa: 94.5%, Tubo de Ventilação: Shepard: 1.9%, Otite Externa Fúngica: 1.5%	Perfuração antiga.	cropped-image.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720577530/fgcfaaf4z4yxmx7qityi.png	\N
4	\N	Otite Media Crônica Simples	f	Otite Média Serosa: 94.5%, Tubo de Ventilação: Shepard: 1.9%, Otite Externa Fúngica: 1.5%	Perfuração antiga.	cropped-image.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720577533/vujnl6ribqo58tioniin.png	\N
5	\N	\N	t	Normal: 71.1%, Não é imagem Otoscópica: 9.4%, Otite Média Aguda - Bacteriana: 5.7%	Surfista	cropped-image.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720578473/bu8g8iwmywamdnaqsedk.png	\N
34	\N	\N	t	Normal: 99.8%, Otite Média Aguda Supurativa/Supurada: 0.1%, Otite Média Crônica - Simples: 0.0%	Pos lavagem ontológica.	normal_998_otite_mdia_aguda_supurativasupurada_01_otite_mdia_crnica__simples_00-1720739157235.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720739157/normal_998_otite_mdia_aguda_supurativasupurada_01_otite_mdia_crnica__simples_00-1720739157235.png.png	\N
35	\N	OTITE EXTERNA AGUDA DIFUSA	f	Otite Média Crônica - Colesteatomatosa/Adesiva: 100.0%, Otite Média Aguda Supurativa/Supurada: 0.0%, Otite Externa Aguda - Difusa: 0.0%	Paciente 9 anos, otalgia 3 dias após banho de piscina	otite_externa_aguda_difusaotite_mdia_crnica__colesteatomatosaadesiva_1000_otite_mdia_aguda_supurativasupurada_00_otite_externa_aguda__difusa_00-1720741744509.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720741744/otite_externa_aguda_difusaotite_mdia_crnica__colesteatomatosaadesiva_1000_otite_mdia_aguda_supurativasupurada_00_otite_externa_aguda__difusa_00-1720741744509.png.png	\N
67	\N	\N	t	Normal: 100.0%, Otite Média Crônica - Simples: 0.0%, Otite Externa Aguda - Difusa: 0.0%	Paciente sem queixas	normal_1000_otite_mdia_crnica__simples_00_otite_externa_aguda__difusa_00-1720803592114.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720803592/normal_1000_otite_mdia_crnica__simples_00_otite_externa_aguda__difusa_00-1720803592114.png.png	\N
68	\N	\N	t	Normal: 100.0%, Otite Média Crônica - Simples: 0.0%, Otite Externa Aguda - Difusa: 0.0%	Paciente sem queixas	normal_1000_otite_mdia_crnica__simples_00_otite_externa_aguda__difusa_00-1720803602931.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720803603/normal_1000_otite_mdia_crnica__simples_00_otite_externa_aguda__difusa_00-1720803602931.png.png	\N
69	\N	Otite Media Serosa	f	Pós Operatório: Timpanoplastia: 76.7%, Otite Média Crônica - Colesteatomatosa/Adesiva: 11.0%, Otite Média Serosa: 9.4%	Plenitude Aural	otite_media_serosaps_operatrio_timpanoplastia_767_otite_mdia_crnica__colesteatomatosaadesiva_110_otite_mdia_serosa_94-1720816038798.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720816039/otite_media_serosaps_operatrio_timpanoplastia_767_otite_mdia_crnica__colesteatomatosaadesiva_110_otite_mdia_serosa_94-1720816038798.png.png	\N
70	\N	Otite Media Serosa	f	Pós Operatório: Timpanoplastia: 98.2%, Otite Média Crônica - Colesteatomatosa/Adesiva: 1.3%, Otite Externa Fúngica: 0.2%	\N	otite_media_serosaps_operatrio_timpanoplastia_982_otite_mdia_crnica__colesteatomatosaadesiva_13_otite_externa_fngica_02-1720816206317.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720816206/otite_media_serosaps_operatrio_timpanoplastia_982_otite_mdia_crnica__colesteatomatosaadesiva_13_otite_externa_fngica_02-1720816206317.png.png	\N
71	\N	\N	t	Otite Externa Aguda - Difusa: 99.9%, Pós Operatório: Timpanoplastia: 0.1%, Otite Média Aguda - Viral ou Inicial: 0.0%	Otalgia pós exposição aquatica	otite_externa_aguda__difusa_999_ps_operatrio_timpanoplastia_01_otite_mdia_aguda__viral_ou_inicial_00-1720816695963.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720816696/otite_externa_aguda__difusa_999_ps_operatrio_timpanoplastia_01_otite_mdia_aguda__viral_ou_inicial_00-1720816695963.png.png	\N
72	\N	Otite Média Aguda	f	Pós Operatório: Timpanoplastia: 76.3%	\N	otite_mdia_agudaps_operatrio_timpanoplastia_763-1720819082937.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720819083/otite_mdia_agudaps_operatrio_timpanoplastia_763-1720819082937.png.png	\N
73	\N	\N	t	Otite Externa Aguda - Difusa: 97.8%	Otalgia 	otite_externa_aguda__difusa_978-1720820547193.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720820547/otite_externa_aguda__difusa_978-1720820547193.png.png	\N
74	\N	Otite Media Serosa	f	Otite Média Crônica - Colesteatomatosa/Adesiva: 58.7%	Plenitude Aural	otite_media_serosaotite_mdia_crnica__colesteatomatosaadesiva_587-1720832503347.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720832503/otite_media_serosaotite_mdia_crnica__colesteatomatosaadesiva_587-1720832503347.png.png	Pós Operatório: Timpanoplastia: 26.5%, Otite Média Serosa: 8.3%, Otite Externa Fúngica: 4.2%
75	\N	\N	t	Otite Externa Localizada: 64.6%	Timpanoesclerose	otite_externa_localizada_646-1720834047849.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720834047/otite_externa_localizada_646-1720834047849.png.png	Otite Externa Aguda - Difusa: 17.9%, Cerume Impactado: 13.2%, Otite Média Crônica - Simples: 2.3%
76	\N	\N	t	Normal: 100.0%	\N	normal_1000-1720879459823.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720879459/normal_1000-1720879459823.png.png	Otite Média Aguda - Bacteriana: 0.0%, Otite Externa Localizada: 0.0%, Cerume Impactado: 0.0%
77	\N	\N	t	Normal: 100.0%	sem dor	normal_1000-1720887919720.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1720887919/normal_1000-1720887919720.png.png	Otite Média Aguda - Bacteriana: 0.0%, Timpanoescle: 0.0%, Otite Externa Localizada: 0.0%
78	\N	Corpo Estranho 	f	Otite Externa Localizada: 75.3%	Chiclete no ouvido	corpo_estranho_otite_externa_localizada_753-1721063415516.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1721063415/corpo_estranho_otite_externa_localizada_753-1721063415516.png.png	Otite Externa Localizada: 11.7%, Otite Externa Localizada: 9.1%, Corpo Estranho: 3.5%
100	\N	\N	t	Otite Média Aguda - Bacteriana: 97.0%	paciten	otite_mdia_aguda__bacteriana_970-1726939259852.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1726939259/otite_mdia_aguda__bacteriana_970-1726939259852.png.png	Otite Média Aguda - Bacteriana: 2.0%, Otite Média Aguda - Bacteriana: 0.6%, Cerume Impactado: 0.5%
133	\N	oma	f	Otite Externa Localizada: 45.4%	\N	omaotite_externa_localizada_454-1749944273095.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1749944273/omaotite_externa_localizada_454-1749944273095.png.png	Otite Externa Localizada: 32.4%, Otite Média Aguda - Bacteriana: 11.4%, Normal: 3.9%
134	\N	oma	f	Otite Externa Localizada: 45.4%	\N	omaotite_externa_localizada_454-1749944274728.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1749944274/omaotite_externa_localizada_454-1749944274728.png.png	Otite Externa Localizada: 32.4%, Otite Média Aguda - Bacteriana: 11.4%, Normal: 3.9%
166	\N	Normal	f	Corpo Estranho: 51.9%	\N	normalcorpo_estranho_519-1753730926992.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1753730927/normalcorpo_estranho_519-1753730926992.png.png	Tubo de Ventilação: Shepard: 24.7%, Normal: 23.2%, Timpanoescle: 0.1%
167	\N	Otite media aguda 	f	Normal: 98.5%	\N	otite_media_aguda_normal_985-1754576224686.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1754576224/otite_media_aguda_normal_985-1754576224686.png.png	Otite Média Aguda - Bacteriana: 1.5%, Otite Média Aguda - Bacteriana: 0.0%, Timpanoescle: 0.0%
199	\N	otite média cronica	f	Otite Média Aguda - Bacteriana: 86.6%	perfuração antiga	otite_mdia_cronicaotite_mdia_aguda__bacteriana_866-1768859271252.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1768859271/otite_mdia_cronicaotite_mdia_aguda__bacteriana_866-1768859271252.png.png	Cerume Impactado: 7.3%, Otite Externa Localizada: 3.8%, Otite Média Aguda - Bacteriana: 1.2%
232	\N	\N	t	Normal: 58.4%	\N	normal_584-1773628239080.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1773628239/normal_584-1773628239080.png.png	Otite Externa Localizada: 18.0%, Otite Média Aguda - Bacteriana: 17.0%, Otite Média Aguda - Bacteriana: 4.5%
265	\N	OTITE MEDIA AGUDA	f	Normal: 100.0%	SECREÇÂO PURULENTA EM CAIXA TIMPANICA POS VIRAL	otite_media_agudanormal_1000-1774889754219.png	https://res.cloudinary.com/dzfsjokbo/image/upload/v1774889754/otite_media_agudanormal_1000-1774889754219.png.png	Corpo Estranho: 0.0%, Tubo de Ventilação: Shepard: 0.0%, Timpanoescle: 0.0%
\.


--
-- Name: feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: u15smncfh5gol7
--

SELECT pg_catalog.setval('public.feedback_id_seq', 265, true);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: u15smncfh5gol7
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: u15smncfh5gol7
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- Name: FUNCTION pg_stat_statements_reset(userid oid, dbid oid, queryid bigint); Type: ACL; Schema: public; Owner: rdsadmin
--

GRANT ALL ON FUNCTION public.pg_stat_statements_reset(userid oid, dbid oid, queryid bigint) TO u15smncfh5gol7;


--
-- Name: extension_before_drop; Type: EVENT TRIGGER; Schema: -; Owner: heroku_admin
--

CREATE EVENT TRIGGER extension_before_drop ON ddl_command_start
   EXECUTE FUNCTION _heroku.extension_before_drop();


ALTER EVENT TRIGGER extension_before_drop OWNER TO heroku_admin;

--
-- Name: log_create_ext; Type: EVENT TRIGGER; Schema: -; Owner: heroku_admin
--

CREATE EVENT TRIGGER log_create_ext ON ddl_command_end
   EXECUTE FUNCTION _heroku.create_ext();


ALTER EVENT TRIGGER log_create_ext OWNER TO heroku_admin;

--
-- Name: log_drop_ext; Type: EVENT TRIGGER; Schema: -; Owner: heroku_admin
--

CREATE EVENT TRIGGER log_drop_ext ON sql_drop
   EXECUTE FUNCTION _heroku.drop_ext();


ALTER EVENT TRIGGER log_drop_ext OWNER TO heroku_admin;

--
-- Name: validate_extension; Type: EVENT TRIGGER; Schema: -; Owner: heroku_admin
--

CREATE EVENT TRIGGER validate_extension ON ddl_command_end
   EXECUTE FUNCTION _heroku.validate_extension();


ALTER EVENT TRIGGER validate_extension OWNER TO heroku_admin;

--
-- PostgreSQL database dump complete
--

