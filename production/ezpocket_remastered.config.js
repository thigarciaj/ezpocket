// Caminho base do projeto - altere apenas esta linha se mudar de localização
const BASE_PATH = "/home/servidores/ezpocket";
const PYTHON_PATH = `${BASE_PATH}/ezinho_assistente/bin/python`;

module.exports = {
  apps: [
    // Graph Orchestrator WebSocket Server
    {
      name: "graph-orchestrator-websocket",
      script: "agents/graph_orchestrator/test_endpoint_websocket.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "512M",
      env: {
        PYTHONPATH: BASE_PATH,
        NODE_ENV: "production"
      },
      out_file: "/var/log/pm2/graph-orchestrator-websocket.out.log",
      error_file: "/var/log/pm2/graph-orchestrator-websocket.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 1: Intent Validator
    {
      name: "worker-intent-validator",
      script: "agents/graph_orchestrator/worker_intent_validator.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-intent-validator.out.log",
      error_file: "/var/log/pm2/worker-intent-validator.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 2: Plan Builder
    {
      name: "worker-plan-builder",
      script: "agents/graph_orchestrator/worker_plan_builder.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-plan-builder.out.log",
      error_file: "/var/log/pm2/worker-plan-builder.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 3: Plan Confirm
    {
      name: "worker-plan-confirm",
      script: "agents/graph_orchestrator/worker_plan_confirm.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-plan-confirm.out.log",
      error_file: "/var/log/pm2/worker-plan-confirm.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 4: User Proposed Plan
    {
      name: "worker-user-proposed-plan",
      script: "agents/graph_orchestrator/worker_user_proposed_plan.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-user-proposed-plan.out.log",
      error_file: "/var/log/pm2/worker-user-proposed-plan.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 5: Plan Refiner
    {
      name: "worker-plan-refiner",
      script: "agents/graph_orchestrator/worker_plan_refiner.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-plan-refiner.out.log",
      error_file: "/var/log/pm2/worker-plan-refiner.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 6: Analysis Orchestrator
    {
      name: "worker-analysis-orchestrator",
      script: "agents/graph_orchestrator/worker_analysis_orchestrator.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "384M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-analysis-orchestrator.out.log",
      error_file: "/var/log/pm2/worker-analysis-orchestrator.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 7: SQL Validator
    {
      name: "worker-sql-validator",
      script: "agents/graph_orchestrator/worker_sql_validator.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-sql-validator.out.log",
      error_file: "/var/log/pm2/worker-sql-validator.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 8: Auto Correction
    {
      name: "worker-auto-correction",
      script: "agents/graph_orchestrator/worker_auto_correction.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "384M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-auto-correction.out.log",
      error_file: "/var/log/pm2/worker-auto-correction.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 9: Athena Executor
    {
      name: "worker-athena-executor",
      script: "agents/graph_orchestrator/worker_athena_executor.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "384M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-athena-executor.out.log",
      error_file: "/var/log/pm2/worker-athena-executor.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 10: Python Runtime
    {
      name: "worker-python-runtime",
      script: "agents/graph_orchestrator/worker_python_runtime.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "512M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-python-runtime.out.log",
      error_file: "/var/log/pm2/worker-python-runtime.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 11: Response Composer
    {
      name: "worker-response-composer",
      script: "agents/graph_orchestrator/worker_response_composer.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-response-composer.out.log",
      error_file: "/var/log/pm2/worker-response-composer.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 12: User Feedback
    {
      name: "worker-user-feedback",
      script: "agents/graph_orchestrator/worker_user_feedback.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-user-feedback.out.log",
      error_file: "/var/log/pm2/worker-user-feedback.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    },

    // Worker 13: History Preferences
    {
      name: "worker-history-preferences",
      script: "agents/graph_orchestrator/worker_history_preferences.py",
      interpreter: PYTHON_PATH,
      cwd: BASE_PATH,
      autorestart: true,
      watch: false,
      max_memory_restart: "256M",
      env: {
        PYTHONPATH: BASE_PATH
      },
      out_file: "/var/log/pm2/worker-history-preferences.out.log",
      error_file: "/var/log/pm2/worker-history-preferences.err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    }
  ]
};