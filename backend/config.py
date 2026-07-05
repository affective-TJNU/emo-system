
import os
from datetime import timedelta

class Config:
    """基础配置类"""
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    RESULTS_FOLDER = 'results'
    LOGS_FOLDER = 'logs'
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'eeg', 'edf', 'bdf', 'mat', 'csv', 'txt'}
    
    # 数据库配置（如果需要）
    DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///emotion_system.db'
    
    # 模型配置（与 models/registry.py 保持一致）
    MODEL_CONFIG = {
        'model_name': 'CADD_DCCNN',
        'architecture': 'Attention-based Temporal Graph Reasoning Network',
        'input_channels': 64,
        'sampling_rate': 1000,
        'epochs': 30,
        'batch_size': 32,
        'learning_rate': 0.001,
        'dropout': 0.5
    }
    
    # 情绪类别
    EMOTION_CLASSES = ['positive', 'neutral', 'negative']
    
    # 频带配置
    FREQUENCY_BANDS = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30),
        'gamma': (30, 100)
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    DEVELOPMENT = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}













