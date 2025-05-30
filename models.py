from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
import datetime

Base = declarative_base()


class Collection(Base):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True)
    collection_id = Column(String(50), unique=True, nullable=False)
    collection_date = Column(Date)
    location = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    collector = Column(String(100))
    habitat = Column(String(200))
    notes = Column(Text)

    # 现有的字段
    family = Column(String(100))  # 科
    family_chinese = Column(String(100))  # 科中文名
    genus = Column(String(100))  # 属
    genus_chinese = Column(String(100))  # 属中文名
    species_latin = Column(String(100))  # 种拉丁名
    species_chinese = Column(String(100))  # 种中文名
    common_name = Column(String(100))  # 俗名
    identified = Column(Boolean, default=False)  # 是否已鉴定
    identified_by = Column(String(100))  # 鉴定人
    identified_date = Column(Date)  # 鉴定日期
    identification_notes = Column(Text)  # 鉴定备注
    original_id = Column(String(50))  # 原始编号


    # 其他应该存在的字段
    country = Column(String(100))  # 国家
    terrain = Column(String(100))  # 地形
    land_use = Column(String(100))  # 土地利用
    soil_parent_material = Column(String(100))  # 土壤母质
    soil_texture = Column(String(100))  # 土壤质地
    seed_harvest_period = Column(String(100))  # 收获种子时期
    collection_part = Column(String(100))  # 采集部位
    seed_quantity = Column(Integer)  # 种子数量
    seed_condition = Column(String(100))  # 种子状况
    fruit_size = Column(String(100))  # 果实大小
    fruit_color = Column(String(100))  # 果实颜色
    specimen_number = Column(String(100))  # 标本号

    seed_batches = relationship("SeedBatch", back_populates="collection")
    cultivation_records = relationship("CultivationRecord", back_populates="collection")
    images = relationship("CollectionImage", back_populates="collection")


class CollectionImage(Base):
    __tablename__ = 'collection_images'

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    file_path  = Column(String(200))
    description = Column(Text)
    upload_date = Column(Date, default=datetime.datetime.now)

    collection = relationship("Collection", back_populates="images")


class SeedBatch(Base):
    __tablename__ = 'seed_batches'

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), unique=True, nullable=False)  # 批次编号
    seed_id = Column(String(50))  # 种子编号
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=True)  # 关联采集ID，可以为空
    parent_cultivation_id = Column(Integer, ForeignKey('cultivation_records.id'), nullable=True)  # 关联母本栽培
    species_chinese = Column(String(100))  # 种子名称
    species_latin = Column(String(100))  # 拉丁学名
    quantity = Column(Integer)  # 种子数量
    storage_location = Column(String(200))  # 存储位置
    storage_date = Column(Date)  # 存储日期
    viability = Column(Float)  # 活力/发芽率
    notes = Column(Text)  # 备注
    source = Column(String(50))  # 来源
    weight = Column(Float)  # 重量

    collection = relationship("Collection", back_populates="seed_batches")
    germination_records = relationship("GerminationRecord", back_populates="seed_batch")
    # cultivation_records和parent_cultivation关系在后面定义
    base_images = relationship("BaseImage", back_populates="seed_batch")

class GerminationRecord(Base):
    __tablename__ = 'germination_records'

    id = Column(Integer, primary_key=True)
    germination_id = Column(String(50), unique=True, nullable=False)  # 保育编号
    seed_batch_id = Column(Integer, ForeignKey('seed_batches.id'))  # 关联种子批次
    start_date = Column(Date, default=datetime.datetime.now)  # 开始发芽实验日期
    treatment = Column(String(200))  # 处理方式
    quantity_used = Column(Integer)  # 使用的种子数量
    germinated_count = Column(Integer, default=0)  # 已发芽数量
    germination_rate = Column(Float, default=0.0)  # 发芽率
    status = Column(String(50))  # 状态：进行中/已完成
    notes = Column(Text)  # 备注

    seed_batch = relationship("SeedBatch", back_populates="germination_records")
    germination_events = relationship("GerminationEvent", back_populates="germination_record")
    images = relationship("GerminationImage", back_populates="germination_record")


class GerminationEvent(Base):
    __tablename__ = 'germination_events'
    id = Column(Integer, primary_key=True)
    germination_record_id = Column(Integer, ForeignKey('germination_records.id'))  # 注意这里的字段名应该是germination_record_id而不是germination_id
    event_date = Column(Date, default=datetime.datetime.now)
    count = Column(Integer)  # 新发芽数量
    cumulative_count = Column(Integer)  # 累计发芽数量
    notes = Column(Text)

    germination_record = relationship("GerminationRecord", back_populates="germination_events")


class GerminationImage(Base):
    __tablename__ = 'germination_images'

    id = Column(Integer, primary_key=True)
    germination_id = Column(Integer, ForeignKey('germination_records.id'))
    file_path = Column(String(200))
    description = Column(Text)

    germination_record = relationship("GerminationRecord", back_populates="images")


class CultivationRecord(Base):
    __tablename__ = 'cultivation_records'

    id = Column(Integer, primary_key=True)
    cultivation_id = Column(String(50), unique=True, nullable=False)  # 栽培编号
    seed_batch_id = Column(Integer, ForeignKey('seed_batches.id'), nullable=True)  # 关联种子批次
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=True)  # 直接关联野外采集
    parent_cultivation_id = Column(Integer, ForeignKey('cultivation_records.id'), nullable=True)  # 关联母本栽培
    species_chinese = Column(String(100))  # 物种名称
    species_latin = Column(String(100))  # 拉丁学名
    quantity = Column(Integer)  # 数量
    planting_date = Column(Date)  # 栽培日期
    location = Column(String(200))  # 栽培地点
    status = Column(String(50))  # 状态：生长中/已死亡/已收获
    notes = Column(Text)  # 备注
    substrate = Column(String(100))  # 基质
    container = Column(String(100))  # 容器
    light_condition = Column(String(100))  # 光照条件
    temperature = Column(String(100))  # 温度条件
    watering_regime = Column(String(100))  # 浇水制度
    fertilizer = Column(String(100))  # 肥料

    # Add these missing fields
    start_date = Column(Date, default=datetime.datetime.now)  # 开始日期
    flowering = Column(Boolean, default=False)  # 是否开花
    flowering_date = Column(Date)  # 开花日期
    fruiting = Column(Boolean, default=False)  # 是否结果
    fruiting_date = Column(Date)  # 结果日期
    death_date = Column(Date)  # 死亡日期
    death_reason = Column(Text)  # 死亡原因
    origin = Column(String(100))  # 来源
    origin_details = Column(Text)  # 来源详情

    # Additional taxonomic fields
    family = Column(String(100))  # 科
    family_chinese = Column(String(100))  # 科中文名
    genus = Column(String(100))  # 属
    genus_chinese = Column(String(100))  # 属中文名


    collection = relationship("Collection", back_populates="cultivation_records")

    # 自引用关系
    child_cultivations = relationship("CultivationRecord",
                                      foreign_keys=[parent_cultivation_id],
                                      backref=backref("parent_cultivation", remote_side=[id]))

    cultivation_events = relationship("CultivationEvent", back_populates="cultivation_record")
    images = relationship("CultivationImage", back_populates="cultivation_record")
    subgroups = relationship("CultivationSubgroup", back_populates="cultivation_record")
    plant_images = relationship("PlantImage", back_populates="cultivation_record")

    # seed_batch关系在后面定义
    # harvested_seeds关系在后面定义


class CultivationEvent(Base):
    __tablename__ = 'cultivation_events'

    id = Column(Integer, primary_key=True)
    cultivation_record_id = Column(Integer, ForeignKey('cultivation_records.id'))
    event_date = Column(Date, default=datetime.datetime.now)
    event_type = Column(String(50))  # 事件类型：浇水/施肥/修剪等
    description = Column(Text)

    cultivation_record = relationship("CultivationRecord", back_populates="cultivation_events")


class CultivationImage(Base):
    __tablename__ = 'cultivation_images'

    id = Column(Integer, primary_key=True)
    cultivation_id = Column(Integer, ForeignKey('cultivation_records.id'))
    file_path = Column(String(200))
    description = Column(Text)
    upload_date = Column(Date, default=datetime.datetime.now)

    cultivation_record = relationship("CultivationRecord", back_populates="images")


class CultivationSubgroup(Base):
    __tablename__ = 'cultivation_subgroups'

    id = Column(Integer, primary_key=True)
    cultivation_id = Column(Integer, ForeignKey('cultivation_records.id'))
    quantity = Column(Integer)
    status = Column(String(50))
    status_date = Column(Date, default=datetime.datetime.now)
    notes = Column(Text)

    cultivation_record = relationship("CultivationRecord", back_populates="subgroups")


# 解决循环引用问题，在所有类定义后添加关系
SeedBatch.cultivation_records = relationship("CultivationRecord",
                                             foreign_keys="CultivationRecord.seed_batch_id",
                                             back_populates="seed_batch")
CultivationRecord.seed_batch = relationship("SeedBatch",
                                            foreign_keys="CultivationRecord.seed_batch_id",
                                            back_populates="cultivation_records")

SeedBatch.parent_cultivation = relationship("CultivationRecord",
                                            foreign_keys="SeedBatch.parent_cultivation_id",
                                            back_populates="harvested_seeds")
CultivationRecord.harvested_seeds = relationship("SeedBatch",
                                                 foreign_keys="SeedBatch.parent_cultivation_id",
                                                 back_populates="parent_cultivation")


class BaseImage(Base):
    __tablename__ = 'base_images'
    id = Column(Integer, primary_key=True)
    seed_batch_id = Column(Integer, ForeignKey('seed_batches.id'), nullable=True)  # 关联种子批次
    file_path = Column(String(200))
    description = Column(Text)
    image_date = Column(Date, default=datetime.datetime.now)

    seed_batch = relationship("SeedBatch", back_populates="base_images")


class PlantImage(Base):
    __tablename__ = 'plant_images'

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('cultivation_records.id'), nullable=True)
    file_path = Column(String(200))
    description = Column(Text)
    image_date = Column(Date, default=datetime.datetime.now)

    cultivation_record = relationship("CultivationRecord", back_populates="plant_images")

class SeedImage(Base):
    __tablename__ = 'seed_images'

    id = Column(Integer, primary_key=True)
    seed_batch_id = Column(Integer, ForeignKey('seed_batches.id'))
    file_path = Column(String(200))
    description = Column(Text)
    upload_date = Column(Date, default=datetime.datetime.now)

    seed_batch = relationship("SeedBatch", backref="images")
