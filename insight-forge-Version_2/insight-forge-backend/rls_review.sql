BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 2f1b40cac3be

CREATE TABLE tenants (
    tenant_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    tenant_slug VARCHAR(64) NOT NULL, 
    tenant_name VARCHAR(255) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT pk_tenants PRIMARY KEY (tenant_id), 
    CONSTRAINT uq_tenants_tenant_slug UNIQUE (tenant_slug)
);

CREATE TABLE cohorts (
    cohort_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    tenant_id UUID NOT NULL, 
    cohort_code VARCHAR(32) NOT NULL, 
    department_scope VARCHAR(128) NOT NULL, 
    CONSTRAINT pk_cohorts PRIMARY KEY (cohort_id), 
    CONSTRAINT fk_cohorts_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (tenant_id) ON DELETE RESTRICT
);

CREATE TABLE users (
    user_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    tenant_id UUID NOT NULL, 
    corporate_email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    assigned_role VARCHAR(32) NOT NULL, 
    is_mfa_enabled BOOLEAN DEFAULT true NOT NULL, 
    totp_secret VARCHAR(128), 
    CONSTRAINT pk_users PRIMARY KEY (user_id), 
    CONSTRAINT ck_users_assigned_role CHECK (assigned_role IN ('Admin', 'Dean', 'Faculty', 'Student')), 
    CONSTRAINT fk_users_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (tenant_id) ON DELETE RESTRICT, 
    CONSTRAINT uq_users_corporate_email UNIQUE (corporate_email)
);

CREATE TABLE coaching_interventions (
    intervention_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    tenant_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    faculty_user_id UUID NOT NULL, 
    intervention_notes TEXT NOT NULL, 
    recorded_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CONSTRAINT pk_coaching_interventions PRIMARY KEY (intervention_id), 
    CONSTRAINT fk_coaching_interventions_faculty_user_id_users FOREIGN KEY(faculty_user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_coaching_interventions_student_user_id_users FOREIGN KEY(student_user_id) REFERENCES users (user_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_coaching_interventions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (tenant_id) ON DELETE RESTRICT
);

CREATE INDEX ix_coaching_interventions_tenant_student_recorded ON coaching_interventions (tenant_id, student_user_id, recorded_timestamp);

CREATE TABLE sessions (
    session_id UUID DEFAULT gen_random_uuid() NOT NULL, 
    user_id UUID NOT NULL, 
    tenant_id UUID NOT NULL, 
    jwt_jti VARCHAR(255) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ingress_ip INET NOT NULL, 
    CONSTRAINT pk_sessions PRIMARY KEY (session_id), 
    CONSTRAINT fk_sessions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (tenant_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_sessions_user_id_users FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_sessions_jwt_jti UNIQUE (jwt_jti)
);

CREATE TABLE student_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY, 
    tenant_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    cohort_id UUID NOT NULL, 
    raw_average_grade NUMERIC(5, 2) NOT NULL, 
    normalized_grade_score NUMERIC(5, 2), 
    attendance_percentage NUMERIC(5, 2) NOT NULL, 
    success_indicator_status VARCHAR(24) NOT NULL, 
    reporting_period VARCHAR(32) NOT NULL, 
    CONSTRAINT pk_student_metrics PRIMARY KEY (metric_id), 
    CONSTRAINT ck_student_metrics_success_indicator_status CHECK (success_indicator_status IN ('Safe', 'Amber', 'Critical')), 
    CONSTRAINT ck_student_metrics_attendance_percentage_range CHECK (attendance_percentage >= 0 AND attendance_percentage <= 100.00), 
    CONSTRAINT ck_student_metrics_raw_average_grade_range CHECK (raw_average_grade >= 0 AND raw_average_grade <= 100.00), 
    CONSTRAINT fk_student_metrics_cohort_id_cohorts FOREIGN KEY(cohort_id) REFERENCES cohorts (cohort_id) ON DELETE RESTRICT, 
    CONSTRAINT fk_student_metrics_student_user_id_users FOREIGN KEY(student_user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT fk_student_metrics_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (tenant_id) ON DELETE RESTRICT
);

CREATE INDEX ix_student_metrics_tenant_cohort_status ON student_metrics (tenant_id, cohort_id, success_indicator_status);

CREATE INDEX ix_student_metrics_tenant_grade ON student_metrics (tenant_id, normalized_grade_score DESC);

INSERT INTO alembic_version (version_num) VALUES ('2f1b40cac3be') RETURNING alembic_version.version_num;

-- Running upgrade 2f1b40cac3be -> c0e1fca26f23

ALTER TABLE "users" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "users" FORCE ROW LEVEL SECURITY;

CREATE POLICY users_tenant_isolation
            ON "users"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            );

ALTER TABLE "sessions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "sessions" FORCE ROW LEVEL SECURITY;

CREATE POLICY sessions_tenant_isolation
            ON "sessions"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            );

ALTER TABLE "cohorts" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "cohorts" FORCE ROW LEVEL SECURITY;

CREATE POLICY cohorts_tenant_isolation
            ON "cohorts"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            );

ALTER TABLE "student_metrics" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "student_metrics" FORCE ROW LEVEL SECURITY;

CREATE POLICY student_metrics_tenant_isolation
            ON "student_metrics"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            );

ALTER TABLE "coaching_interventions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "coaching_interventions" FORCE ROW LEVEL SECURITY;

CREATE POLICY coaching_interventions_tenant_isolation
            ON "coaching_interventions"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            );

UPDATE alembic_version SET version_num='c0e1fca26f23' WHERE alembic_version.version_num = '2f1b40cac3be';

COMMIT;

