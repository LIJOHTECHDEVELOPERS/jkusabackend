module.exports = {
  apps: [
    {
      name: 'jkusa-auth',
      script: './server.js',
      env: {
        NODE_ENV: 'production',
        PORT: 3007,
      },
      instances: 'max', // Use all available CPU cores
      exec_mode: 'cluster', // Run in cluster mode for better performance
      autorestart: true, // Automatically restart on crash
      watch: false, // Disable watch in production
      max_memory_restart: '1G', // Restart if memory usage exceeds 1GB
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/error.log',
      out_file: './logs/out.log',
      merge_logs: true,
      time: true,
    },
  ],
};