from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
from models import (
    Base, Collection, GerminationRecord, GerminationEvent,
    CultivationRecord, CultivationEvent, BaseImage, PlantImage, CollectionImage,
    SeedImage, GerminationImage, CultivationImage, SeedBatch, CultivationSubgroup
)
import datetime
import uuid
import os
import qrcode
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from sqlalchemy.sql import func


# 获取当前脚本所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'plant_conservation.db')

# 创建数据库连接
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(engine)

    # 创建图片存储目录
    os.makedirs('static/images/plants', exist_ok=True)
    os.makedirs('static/images/collections', exist_ok=True)
    os.makedirs('static/images/seeds', exist_ok=True)
    os.makedirs('static/images/germination', exist_ok=True)
    os.makedirs('static/images/cultivation', exist_ok=True)

    # 创建条形码和二维码存储目录
    os.makedirs('static/barcodes', exist_ok=True)
    os.makedirs('static/qrcodes', exist_ok=True)


def generate_id(prefix, date=None):
    """生成唯一ID：前缀+日期+随机码"""
    if date is None:
        date = datetime.datetime.now()
    date_str = date.strftime('%Y%m%d')
    random_str = str(uuid.uuid4().hex)[:6].upper()
    return f"{prefix}-{date_str}-{random_str}"


# 原有的添加植物、添加采集和添加种子批次函数保持不变，以下是新增函数

def add_germination_record(seed_batch_id, start_date, treatment, quantity_used, notes=None):
    """添加发芽记录"""
    session = Session()
    germination_id = generate_id("GER")

    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

    germination_record = GerminationRecord(
        germination_id=germination_id,
        seed_batch_id=seed_batch_id,
        start_date=start_date,
        treatment=treatment,
        quantity_used=quantity_used,
        status="进行中",
        notes=notes
    )

    session.add(germination_record)
    session.commit()
    record_id = germination_record.id
    session.close()
    return record_id


def add_germination_event(germination_record_id, event_date, count, notes=None):
    """添加发芽事件"""
    session = Session()

    if isinstance(event_date, str):
        event_date = datetime.datetime.strptime(event_date, '%Y-%m-%d').date()

    # 获取当前记录并计算累计发芽数
    germination_record = session.query(GerminationRecord).filter(GerminationRecord.id == germination_record_id).first()

    # 获取之前的事件
    previous_events = session.query(GerminationEvent).filter(
        GerminationEvent.germination_record_id == germination_record_id
    ).order_by(GerminationEvent.event_date).all()

    cumulative_count = count
    if previous_events:
        cumulative_count += previous_events[-1].cumulative_count

    # 创建新事件
    germination_event = GerminationEvent(
        germination_record_id=germination_record_id,
        event_date=event_date,
        count=count,
        cumulative_count=cumulative_count,
        notes=notes
    )

    session.add(germination_event)

    # 更新发芽记录的发芽率
    if germination_record and germination_record.quantity_used > 0:
        germination_record.germinated_count = cumulative_count
        germination_record.germination_rate = cumulative_count / germination_record.quantity_used

    session.commit()
    event_id = germination_event.id
    session.close()
    return event_id


def complete_germination_record(germination_record_id):
    """
    完成发芽记录
    """
    session = Session()
    try:
        # 获取发芽记录
        record = session.query(GerminationRecord).filter(GerminationRecord.id == germination_record_id).first()

        if record:
            # 更新状态为"已完成"
            record.status = "已完成"

            # 确保在session关闭前获取id
            record_id = record.id

            # 提交更改
            session.commit()
            return record_id
        else:
            return None
    except Exception as e:
        session.rollback()
        print(f"完成发芽记录失败: {e}")
        return None
    finally:
        session.close()


# Add to database.py

def add_cultivation_record(seed_batch_id=None, start_date=None, location=None, quantity=None,
                           notes=None, origin=None, origin_details=None, collection_id=None,
                           parent_cultivation_id=None, family=None, family_chinese=None,
                           genus=None, genus_chinese=None, species_chinese=None,
                           species_latin=None):
    """添加栽培记录，支持多种来源"""
    session = Session()
    cultivation_id = generate_id("CUL")

    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

    cultivation_record = CultivationRecord(
        cultivation_id=cultivation_id,
        seed_batch_id=seed_batch_id,
        start_date=start_date,
        location=location,
        quantity=quantity,
        status="活",
        notes=notes,
        origin=origin,
        origin_details=origin_details,
        collection_id=collection_id,
        parent_cultivation_id=parent_cultivation_id,
        family=family,
        family_chinese=family_chinese,
        genus=genus,
        genus_chinese=genus_chinese,
        species_chinese=species_chinese,
        species_latin=species_latin,
    )

    session.add(cultivation_record)
    session.commit()
    record_id = cultivation_record.id
    session.close()
    return record_id


def add_cultivation_subgroup(cultivation_record_id, status, quantity, status_date=None, notes=None):
    """添加栽培子分组记录"""
    session = Session()

    if isinstance(status_date, str):
        status_date = datetime.datetime.strptime(status_date, '%Y-%m-%d').date()
    elif status_date is None:
        status_date = datetime.datetime.now().date()

    # Create the subgroup
    subgroup = CultivationSubgroup(
        cultivation_id=cultivation_record_id,
        quantity=quantity,
        status=status,
        status_date=status_date,
        notes=notes
    )

    session.add(subgroup)

    # Also add a cultivation event to track this status change
    event = CultivationEvent(
        cultivation_record_id=cultivation_record_id,
        event_date=status_date,
        event_type=status,
        description=f"{quantity}株植物{status}: {notes or ''}"
    )

    session.add(event)

    # Update the main record if needed
    record = session.query(CultivationRecord).filter(CultivationRecord.id == cultivation_record_id).first()

    if record:
        if status == "开花" and not record.flowering:
            record.flowering = True
            record.flowering_date = status_date
        elif status == "结果" and not record.fruiting:
            record.fruiting = True
            record.fruiting_date = status_date

    session.commit()
    subgroup_id = subgroup.id
    session.close()
    return subgroup_id


def get_cultivation_subgroups(cultivation_id):
    """获取栽培记录的子分组"""
    session = Session()
    subgroups = session.query(CultivationSubgroup).filter(
        CultivationSubgroup.cultivation_id == cultivation_id
    ).order_by(CultivationSubgroup.status_date).all()
    session.close()
    return subgroups


def get_fruiting_cultivations():
    """获取已结果的栽培记录"""
    session = Session()
    records = session.query(CultivationRecord).filter(
        CultivationRecord.fruiting == True,
        CultivationRecord.status == "活"
    ).all()
    session.close()
    return records


def add_seed_batch_from_cultivation(cultivation_id, quantity, storage_location,
                                   storage_date=None, viability=None, notes=None):
    """从栽培记录添加种子批次"""
    session = Session()

    # Get the cultivation record
    cultivation = session.query(CultivationRecord).filter(CultivationRecord.id == cultivation_id).first()

    if not cultivation:
        session.close()
        return None

    # Create batch ID
    if storage_date is None:
        storage_date = datetime.datetime.now().date()
    elif isinstance(storage_date, str):
        storage_date = datetime.datetime.strptime(storage_date, '%Y-%m-%d').date()

    batch_id = generate_id("SEED", storage_date)

    # Create the seed batch
    seed_batch = SeedBatch(
        batch_id=batch_id,
        parent_cultivation_id=cultivation_id,
        quantity=quantity,
        storage_location=storage_location,
        storage_date=storage_date,
        viability=viability,
        notes=notes,
        source="栽培收获",
        # Copy taxonomic info from cultivation
        species_chinese=cultivation.species_chinese,  # 修改这里
        species_latin=cultivation.species_latin
    )

    session.add(seed_batch)
    session.commit()
    batch_id = seed_batch.id
    session.close()
    return batch_id



def add_cultivation_event(cultivation_record_id, event_date, event_type, description=None):
    """添加栽培事件"""
    session = Session()

    if isinstance(event_date, str):
        event_date = datetime.datetime.strptime(event_date, '%Y-%m-%d').date()

    cultivation_event = CultivationEvent(
        cultivation_record_id=cultivation_record_id,
        event_date=event_date,
        event_type=event_type,
        description=description
    )

    session.add(cultivation_event)
    session.commit()
    event_id = cultivation_event.id
    session.close()
    return event_id


def update_cultivation_status(cultivation_record_id, status, date, reason=None):
    """
    更新栽培记录状态
    """
    session = Session()
    try:
        # 获取栽培记录
        record = session.query(CultivationRecord).filter(CultivationRecord.id == cultivation_record_id).first()

        if record:
            # 保存记录ID，确保在会话关闭前获取
            record_id = record.id

            # 根据不同状态更新不同字段
            if status == "开花":
                record.flowering = True
                record.flowering_date = date
                # 添加开花事件
                event = CultivationEvent(
                    cultivation_record_id=record_id,
                    event_date=date,
                    event_type="开花",
                    description="植物开始开花"
                )
                session.add(event)

            elif status == "结果":
                record.fruiting = True
                record.fruiting_date = date
                # 添加结果事件
                event = CultivationEvent(
                    cultivation_record_id=record_id,
                    event_date=date,
                    event_type="结果",
                    description="植物开始结果"
                )
                session.add(event)

            elif status == "死亡":
                record.status = "死亡"
                record.death_date = date
                record.death_reason = reason
                # 添加死亡事件
                event = CultivationEvent(
                    cultivation_record_id=record_id,
                    event_date=date,
                    event_type="死亡",
                    description=f"植物死亡，原因: {reason or '未知'}"
                )
                session.add(event)

            # 提交更改
            session.commit()
            return record_id
        else:
            return None
    except Exception as e:
        session.rollback()
        print(f"更新栽培状态失败: {e}")
        return None
    finally:
        session.close()


def batch_update_cultivation_status(cultivation_ids, status, date=None, reason=None):
    """批量更新栽培状态"""
    for cultivation_id in cultivation_ids:
        update_cultivation_status(cultivation_id, status, date, reason)
    return True


def update_plant_identification(collection_id, species_latin, family=None, genus=None, identified_by=None,
                                identified_date=None):
    """更新植物鉴定信息"""
    session = Session()
    plant = session.query(Collection).filter(Collection.id == collection_id).first()

    if plant:
        plant.species_latin = species_latin
        plant.family = family
        plant.genus = genus
        plant.identified = True
        plant.identified_by = identified_by

        if identified_date:
            if isinstance(identified_date, str):
                identified_date = datetime.datetime.strptime(identified_date, '%Y-%m-%d').date()
            plant.identified_date = identified_date
        else:
            plant.identified_date = datetime.datetime.now().date()

        session.commit()

    session.close()
    return plant.id if plant else None


# 图片操作函数
def save_image(file, table_type, record_id, description=""):
    """保存图片文件并返回图片ID或图片ID列表"""

    # 检查file是否为列表，如果是列表处理所有文件
    if isinstance(file, list):
        image_ids = []
        for single_file in file:
            image_id = save_single_image(single_file, table_type, record_id, description)
            if image_id:
                image_ids.append(image_id)
        return image_ids  # 返回ID列表
    else:
        # 单个文件处理
        return save_single_image(file, table_type, record_id, description)


def save_single_image(file, table_type, record_id, description=""):
    """处理单个图片文件并返回图片ID"""
    file_extension = file.name.split(".")[-1]

    # 生成唯一文件名，确保不会覆盖
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{random_str}.{file_extension}"

    # 确保图片目录存在
    BASE_DIR= os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(BASE_DIR, f"static/images/{table_type}s")
    os.makedirs(image_dir, exist_ok=True)

    # 保存图片文件
    filepath = os.path.join(image_dir, filename)
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    # 创建图片对象
    session = Session()
    try:
        if table_type == "plant":
            image = PlantImage(file_path=filepath, description=description, plant_id=record_id)
        elif table_type == "collection":
            image = CollectionImage(file_path=filepath, description=description, collection_id=record_id)
        elif table_type == "seed":
            image = SeedImage(file_path=filepath, description=description, seed_batch_id=record_id)
        elif table_type == "germination":
            image = GerminationImage(file_path=filepath, description=description, germination_id=record_id)
        elif table_type == "cultivation":
            image = CultivationImage(file_path=filepath, description=description, cultivation_id=record_id)
        else:
            session.close()
            return None

        session.add(image)
        session.commit()
        image_id = image.id
        session.close()
        return image_id
    except Exception as e:
        session.rollback()
        print(f"保存图片失败: {e}")
        return None
    finally:
        session.close()

def get_images(image_type, record_id):
    """获取图片列表"""
    session = Session()

    if image_type == "plant":
        images = session.query(PlantImage).filter(PlantImage.plant_id == record_id).all()
    elif image_type == "collection":
        images = session.query(CollectionImage).filter(CollectionImage.collection_id == record_id).all()
    elif image_type == "seed":
        images = session.query(SeedImage).filter(SeedImage.seed_batch_id == record_id).all()
    elif image_type == "germination":
        images = session.query(GerminationImage).filter(GerminationImage.germination_id == record_id).all()
    elif image_type == "cultivation":
        images = session.query(CultivationImage).filter(CultivationImage.cultivation_id == record_id).all()
    else:
        images = []

    session.close()
    return images


# 二维码和条形码生成
def generate_qrcode(data, record_id, record_type):
    """生成二维码"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_path = f"static/qrcodes/{record_type}_{record_id}.png"
    img.save(img_path)

    return img_path


def generate_barcode(data, record_id, record_type):
    """生成条形码"""
    EAN = barcode.get_barcode_class('code128')
    ean = EAN(data, writer=ImageWriter())
    img_path = f"static/barcodes/{record_type}_{record_id}"
    ean.save(img_path)

    return f"{img_path}.png"





def get_germination_record_by_id(record_id):
    """通过ID获取发芽记录"""
    session = Session()
    record = session.query(GerminationRecord).filter(GerminationRecord.id == record_id).first()
    session.close()
    return record

# 获取各类记录的函数
def get_germination_records(filter_species=None):
    """获取发芽记录，可选择按种子名称筛选"""
    session = Session()

    if filter_species:
        # 联表查询，根据种子名称筛选
        records = (session.query(GerminationRecord)
                   .join(SeedBatch, GerminationRecord.seed_batch_id == SeedBatch.id)
                   .filter(
            or_(
                SeedBatch.species_chinese.ilike(f'%{filter_species}%'),
                SeedBatch.species_latin.ilike(f'%{filter_species}%')
            )
        )
                   .order_by(GerminationRecord.start_date.desc())
                   .all())
    else:
        # 不筛选，返回所有记录
        records = session.query(GerminationRecord).order_by(GerminationRecord.start_date.desc()).all()

    session.close()
    return records

def get_germination_events(record_id):
    """获取特定发芽记录的所有事件"""
    session = Session()
    events = session.query(GerminationEvent).filter(
        GerminationEvent.germination_record_id == record_id
    ).order_by(GerminationEvent.event_date).all()
    session.close()
    return events


def get_cultivation_records():
    """获取所有栽培记录"""
    session = Session()
    records = session.query(CultivationRecord).all()
    session.close()
    return records


def get_cultivation_record_by_id(record_id):
    """通过ID获取栽培记录"""
    session = Session()
    record = session.query(CultivationRecord).filter(CultivationRecord.id == record_id).first()
    session.close()
    return record


def get_cultivation_events(record_id):
    """获取特定栽培记录的所有事件"""
    session = Session()
    events = session.query(CultivationEvent).filter(
        CultivationEvent.cultivation_record_id == record_id
    ).order_by(CultivationEvent.event_date).all()
    session.close()
    return events


def search_unidentified_plants():
    """搜索未鉴定的植物"""
    session = Session()
    collections  = session.query(Collection).filter(Collection.identified == False).all()
    session.close()
    return collections


def get_seed_batches_for_germination():
    """获取可用于发芽实验的种子批次"""
    session = Session()

    # 找出所有种子批次及其已用于发芽的数量
    seed_batches = session.query(SeedBatch).all()

    result = []
    for batch in seed_batches:
        # 计算已用于发芽的种子数量
        used_seeds = session.query(GerminationRecord).filter(
            GerminationRecord.seed_batch_id == batch.id
        ).with_entities(
            func.sum(GerminationRecord.quantity_used)
        ).scalar() or 0

        # 计算已用于栽培的种子数量
        used_for_cultivation = session.query(CultivationRecord).filter(
            CultivationRecord.seed_batch_id == batch.id
        ).with_entities(
            func.sum(CultivationRecord.quantity)
        ).scalar() or 0

        # 总共使用的种子数量
        total_used = used_seeds + used_for_cultivation

        # 如果还有剩余种子可用
        if batch.quantity > total_used:
            batch.available_quantity = batch.quantity - total_used
            result.append(batch)

    session.close()
    return result

def get_session():
    """
    获取数据库会话
    """
    from sqlalchemy.orm import sessionmaker
    engine = get_engine()  # 假设 get_engine 函数已经存在
    Session = sessionmaker(bind=engine)
    return Session()


# 如果 get_engine 函数也不存在，还需要添加它
def get_engine():
    """
    获取数据库引擎
    """
    from sqlalchemy import create_engine
    # 替换为你的实际数据库连接字符串
    db_path = "sqlite:///plant_conservation.db"  # 或者你实际使用的数据库路径
    return create_engine(db_path)






def get_all_plants():
    """获取所有植物"""
    session = Session()
    collections = session.query(Collection).all()
    session.close()
    return collections


def get_plant_by_id(plant_id):
    """通过ID获取植物，改为获取 Collection"""
    session = Session()
    collection = session.query(Collection).filter(Collection.collection_id == plant_id).first()
    session.close()
    return collection


def get_all_collections():
    """获取所有采集记录"""
    session = Session()
    collections = session.query(Collection).all()
    session.close()
    return collections


def get_seed_batches(filter_species=None):
    """获取种子批次，可选择按种子名称筛选"""
    session = Session()
    query = session.query(SeedBatch)

    if filter_species:
        query = query.filter(
            or_(
                SeedBatch.species_chinese.ilike(f'%{filter_species}%'),
                SeedBatch.species_latin.ilike(f'%{filter_species}%')
            )
        )

    seed_batches = query.order_by(SeedBatch.storage_date.desc()).all()
    session.close()
    return seed_batches

def get_collection_by_id(collection_id):
    """根据ID获取采集记录"""
    session = Session()
    collection = session.query(Collection).filter(Collection.id == collection_id).first()
    session.close()
    return collection

def get_seed_batch_by_id(batch_id):
    """根据ID获取种子批次"""
    session = Session()
    seed_batch = session.query(SeedBatch).filter(SeedBatch.id == batch_id).first()
    session.close()
    return seed_batch

def get_germination_records_by_batch(batch_id):
    """获取某种子批次的所有发芽记录"""
    session = Session()
    records = session.query(GerminationRecord).filter(GerminationRecord.seed_batch_id == batch_id).all()
    session.close()
    return records


def add_seed_batch(collection_id=None, quantity=None, storage_location=None,
                   storage_date=None, viability=None, notes=None, source=None, seed_id=None):
    """添加种子批次"""
    session = Session()
    batch_id = generate_id("SEED", storage_date)
    seed_batch = SeedBatch(
        batch_id=batch_id,
        seed_id=seed_id,
        collection_id=collection_id,
        quantity=quantity,
        storage_location=storage_location,
        storage_date=storage_date,
        viability=viability,
        notes=notes,
        source=source
    )

    # 如果有关联的采集记录，自动填充物种信息
    if collection_id:
        collection = session.query(Collection).filter(Collection.id == collection_id).first()
        if collection:
            seed_batch.species_latin = collection.species_latin
            seed_batch.species_chinese = collection.species_chinese

    session.add(seed_batch)
    session.commit()
    record_id = seed_batch.id
    session.close()
    return record_id

def add_collection(collection_date, location, latitude, longitude, altitude, collector,
                  notes=None, habitat=None, species_latin=None,
                  family=None, family_chinese=None, genus=None, genus_chinese=None,
                  identified=False, original_id=None, country=None,
                  species_chinese=None, terrain=None, land_use=None,
                  soil_parent_material=None, soil_texture=None, seed_harvest_period=None,
                  collection_part=None, seed_quantity=None, seed_condition=None,
                  fruit_size=None, fruit_color=None, specimen_number=None,common_name=None):
    """添加采集记录"""
    session = Session()
    collection_id = generate_id("COL", collection_date)
    collection = Collection(
        collection_id=collection_id,
        original_id=original_id,
        collection_date=collection_date,
        location=location,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        collector=collector,
        common_name=common_name,
        notes=notes,
        habitat=habitat,
        species_latin=species_latin,  # 修改这里
        family=family,
        family_chinese=family_chinese,
        genus=genus,
        genus_chinese=genus_chinese,
        identified=identified,
        country=country,
        species_chinese=species_chinese,
        terrain=terrain,
        land_use=land_use,
        soil_parent_material=soil_parent_material,
        soil_texture=soil_texture,
        seed_harvest_period=seed_harvest_period,
        collection_part=collection_part,
        seed_quantity=seed_quantity,
        seed_condition=seed_condition,
        fruit_size=fruit_size,
        fruit_color=fruit_color,
        specimen_number=specimen_number
    )
    session.add(collection)
    session.commit()
    record_id = collection.id
    session.close()
    return collection_id

def update_collection(collection_id, collection_date=None, location=None, latitude=None,
                      longitude=None, altitude=None, collector=None, notes=None, habitat=None,
                      species_latin=None, family=None, family_chinese=None,
                      genus=None, genus_chinese=None, identified=None,
                      identified_by=None, identified_date=None, original_id=None, country=None,
                      species_chinese=None, terrain=None, land_use=None,
                      soil_parent_material=None, soil_texture=None, seed_harvest_period=None,
                      collection_part=None, seed_quantity=None, seed_condition=None,
                      fruit_size=None, fruit_color=None, specimen_number=None,common_name=None):
    """更新采集记录"""
    session = Session()
    try:
        collection = session.query(Collection).filter(Collection.id == collection_id).first()
        if collection:
            if collection_date is not None:
                collection.collection_date = collection_date
            if collection.common_name is not None:
                collection.common_name = collection.common_name
            if location is not None:
                collection.location = location
            if latitude is not None:
                collection.latitude = latitude
            if longitude is not None:
                collection.longitude = longitude
            if altitude is not None:
                collection.altitude = altitude
            if collector is not None:
                collection.collector = collector
            if notes is not None:
                collection.notes = notes
            if habitat is not None:
                collection.habitat = habitat
            if species_latin is not None:
                collection.species_latin = species_latin
            if species_chinese is not None:
                collection.species_chinese = species_chinese
            if family is not None:
                collection.family = family
            if family_chinese is not None:
                collection.family_chinese = family_chinese
            if genus is not None:
                collection.genus = genus
            if genus_chinese is not None:
                collection.genus_chinese = genus_chinese

            if identified is not None:
                collection.identified = identified
            if identified_by is not None:
                collection.identified_by = identified_by
            if identified_date is not None:
                collection.identified_date = identified_date
            if original_id is not None:
                collection.original_id = original_id
            # 新增字段
            if country is not None:
                collection.country = country
            if terrain is not None:
                collection.terrain = terrain
            if land_use is not None:
                collection.land_use = land_use
            if soil_parent_material is not None:
                collection.soil_parent_material = soil_parent_material
            if soil_texture is not None:
                collection.soil_texture = soil_texture
            if seed_harvest_period is not None:
                collection.seed_harvest_period = seed_harvest_period
            if collection_part is not None:
                collection.collection_part = collection_part
            if seed_quantity is not None:
                collection.seed_quantity = seed_quantity
            if seed_condition is not None:
                collection.seed_condition = seed_condition
            if fruit_size is not None:
                collection.fruit_size = fruit_size
            if fruit_color is not None:
                collection.fruit_color = fruit_color
            if specimen_number is not None:
                collection.specimen_number = specimen_number

            session.commit()
            return True
    except Exception as e:
        session.rollback()
        print(f"更新采集记录失败: {e}")
        return False
    finally:
        session.close()



def update_collection_identification(collection_id,
                                    family=None, family_chinese=None, genus=None, genus_chinese=None,
                                    species_latin=None, identified_by=None, identification_notes=None,
                                    species_chinese=None):
    """更新采集记录的植物鉴定信息"""
    session = Session()
    try:
        collection = session.query(Collection).filter(Collection.id == collection_id).first()
        if collection:
            if species_latin:
                collection.species_latin = species_latin
            if family:
                collection.family = family
            if family_chinese:
                collection.family_chinese = family_chinese
            if genus:
                collection.genus = genus
            if genus_chinese:
                collection.genus_chinese = genus_chinese
            if species_chinese:
                collection.species_chinese = species_chinese
            if identified_by:
                collection.identified_by = identified_by
            if identification_notes:
                collection.identification_notes = identification_notes

            # 如果提供了学名，则标记为已鉴定
            if species_latin:
                collection.identified = True
                collection.identified_date = datetime.datetime.now().date()

            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"更新植物鉴定信息失败: {e}")
        return False
    finally:
        session.close()




def get_unidentified_collections():
    """获取未鉴定的采集记录"""
    session = Session()
    collections = session.query(Collection).filter(Collection.identified == False).all()
    session.close()
    return collections


def search_collections_by_taxonomy(family=None, genus=None, species_latin=None, species_chinese=None):
    """按分类信息搜索采集记录"""
    session = Session()

    filters = []
    if family:
        filters.append(Collection.family.ilike(f'%{family}%'))
    if genus:
        filters.append(Collection.genus.ilike(f'%{genus}%'))
    if species_latin:
        filters.append(Collection.species_latin.ilike(f'%{species_latin}%'))
    if species_chinese:
        filters.append(Collection.species_chinese.ilike(f'%{species_chinese}%'))

    if filters:
        collections = session.query(Collection).filter(or_(*filters)).all()
    else:
        collections = session.query(Collection).all()

    session.close()
    return collections

def update_seed_batch(batch_id, **kwargs):
    """更新种子批次信息"""
    session = Session()
    session.query(SeedBatch).filter(SeedBatch.id == batch_id).update(kwargs)
    session.commit()
    session.close()


def search_plants(search_term, identification_status=None, family=None):
    """搜索植物，改为搜索 Collection"""
    session = Session()
    query = f"%{search_term}%"
    # 构建基本查询条件，使用 Collection 的字段
    filters = [
        or_(
            Collection.species_latin.like(query),
            Collection.species_chinese.like(query),
            Collection.family.like(query),
            Collection.genus.like(query),
            Collection.species_chinese.like(query),
            Collection.collection_id.like(query)
        )
    ]
    # 添加鉴定状态筛选
    if identification_status is not None:
        filters.append(Collection.identified == identification_status)
    # 添加科筛选
    if family:
        filters.append(Collection.family.like(f"%{family}%"))
    # 执行查询
    collections = session.query(Collection).filter(and_(*filters)).all()
    session.close()
    return collections


def update_image_description(image_id, description):
    """更新图片描述"""
    session = Session()
    try:
        # 尝试在不同的图片表中查找图片
        image_found = False

        # 检查CollectionImage表
        image = session.query(CollectionImage).filter(CollectionImage.id == image_id).first()
        if image:
            image.description = description
            image_found = True

        # 检查SeedImage表
        if not image_found:
            image = session.query(SeedImage).filter(SeedImage.id == image_id).first()
            if image:
                image.description = description
                image_found = True

        # 检查GerminationImage表
        if not image_found:
            image = session.query(GerminationImage).filter(GerminationImage.id == image_id).first()
            if image:
                image.description = description
                image_found = True

        # 检查CultivationImage表
        if not image_found:
            image = session.query(CultivationImage).filter(CultivationImage.id == image_id).first()
            if image:
                image.description = description
                image_found = True

        # 检查PlantImage表
        if not image_found:
            image = session.query(PlantImage).filter(PlantImage.id == image_id).first()
            if image:
                image.description = description
                image_found = True

        # 如果都没找到，最后尝试BaseImage表
        if not image_found:
            image = session.query(BaseImage).filter(BaseImage.id == image_id).first()
            if image:
                image.description = description
                image_found = True

        session.commit()
        return image_found
    except Exception as e:
        session.rollback()
        print(f"更新图片描述失败: {e}")
        return False
    finally:
        session.close()


def delete_image(image_id):
    """删除图片"""
    session = Session()
    try:
        # 尝试在不同的图片表中查找图片
        image_found = False
        image_path = None

        # 检查CollectionImage表
        image = session.query(CollectionImage).filter(CollectionImage.id == image_id).first()
        if image:
            image_path = image.file_path
            session.delete(image)
            image_found = True

        # 检查SeedImage表
        if not image_found:
            image = session.query(SeedImage).filter(SeedImage.id == image_id).first()
            if image:
                image_path = image.file_path
                session.delete(image)
                image_found = True

        # 检查GerminationImage表
        if not image_found:
            image = session.query(GerminationImage).filter(GerminationImage.id == image_id).first()
            if image:
                image_path = image.file_path
                session.delete(image)
                image_found = True

        # 检查CultivationImage表
        if not image_found:
            image = session.query(CultivationImage).filter(CultivationImage.id == image_id).first()
            if image:
                image_path = image.file_path
                session.delete(image)
                image_found = True

        # 检查PlantImage表
        if not image_found:
            image = session.query(PlantImage).filter(PlantImage.id == image_id).first()
            if image:
                image_path = image.file_path
                session.delete(image)
                image_found = True

        # 如果都没找到，最后尝试BaseImage表
        if not image_found:
            image = session.query(BaseImage).filter(BaseImage.id == image_id).first()
            if image:
                image_path = image.file_path
                session.delete(image)
                image_found = True

        # 删除文件
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        session.commit()
        return image_found
    except Exception as e:
        session.rollback()
        print(f"删除图片失败: {e}")
        return False
    finally:
        session.close()


def search_collections(start_date, end_date, location=None, collector=None):
    """搜索采集记录"""
    session = Session()

    # 构建过滤条件
    filters = [
        Collection.collection_date >= start_date,
        Collection.collection_date <= end_date
    ]

    if location:
        filters.append(Collection.location.like(f"%{location}%"))

    if collector:
        filters.append(Collection.collector.like(f"%{collector}%"))

    collections = session.query(Collection).filter(*filters).all()
    session.close()
    return collections


def search_seed_batches(start_date, end_date, storage_location=None):
    """搜索种子批次"""
    session = Session()

    # 构建过滤条件
    filters = [
        SeedBatch.storage_date >= start_date,
        SeedBatch.storage_date <= end_date
    ]

    if storage_location:
        filters.append(SeedBatch.storage_location.like(f"%{storage_location}%"))

    seed_batches = session.query(SeedBatch).filter(*filters).all()
    session.close()
    return seed_batches


def search_germination_records(start_date, end_date, status=None, treatment=None):
    """搜索发芽记录"""
    session = Session()

    # 构建过滤条件
    filters = [
        GerminationRecord.start_date >= start_date,
        GerminationRecord.start_date <= end_date
    ]

    if status:
        filters.append(GerminationRecord.status == status)

    if treatment:
        filters.append(GerminationRecord.treatment.like(f"%{treatment}%"))

    records = session.query(GerminationRecord).filter(*filters).all()
    session.close()
    return records


def search_cultivation_records(start_date, end_date, status=None, location=None):
    """搜索栽培记录"""
    session = Session()

    # 构建过滤条件
    filters = [
        CultivationRecord.start_date >= start_date,
        CultivationRecord.start_date <= end_date
    ]

    if status:
        filters.append(CultivationRecord.status == status)

    if location:
        filters.append(CultivationRecord.location.like(f"%{location}%"))

    records = session.query(CultivationRecord).filter(*filters).all()
    session.close()
    return records


def get_all_families():
    """获取所有科，改为从 Collection 获取"""
    session = Session()
    families = session.query(Collection.family).distinct().filter(Collection.family != None).order_by(
        Collection.family).all()
    session.close()
    return [f[0] for f in families if f[0]]


def get_all_genera():
    """获取所有属，改为从 Collection 获取"""
    session = Session()
    genera = session.query(Collection.genus).distinct().filter(Collection.genus != None).order_by(
        Collection.genus).all()
    session.close()
    return [g[0] for g in genera if g[0]]


def get_plants_by_family(family):
    """按科获取植物，改为获取 Collection"""
    session = Session()
    collections = session.query(Collection).filter(Collection.family == family).all()
    session.close()
    return collections


def get_plants_by_genus(genus):
    """按属获取植物，改为获取 Collection"""
    session = Session()
    collections = session.query(Collection).filter(Collection.genus == genus).all()
    session.close()
    return collections



def get_seed_batches_by_collection(collection_id):
    """获取指定采集记录的种子批次"""
    session = Session()
    batches = session.query(SeedBatch).filter(SeedBatch.collection_id == collection_id).all()

    # 计算每个批次的可用数量
    for batch in batches:
        # 计算已用于发芽的种子数量
        used_seeds = session.query(GerminationRecord).filter(
            GerminationRecord.seed_batch_id == batch.id
        ).with_entities(
            func.sum(GerminationRecord.quantity_used)
        ).scalar() or 0

        # 计算已用于栽培的种子数量
        used_for_cultivation = session.query(CultivationRecord).filter(
            CultivationRecord.seed_batch_id == batch.id
        ).with_entities(
            func.sum(CultivationRecord.quantity)
        ).scalar() or 0

        # 总共使用的种子数量
        total_used = used_seeds + used_for_cultivation

        # 计算可用数量
        batch.available_quantity = batch.quantity - total_used if batch.quantity else 0

    session.close()
    return batches

def show_cultivation_statistics():
    st.subheader("栽培统计")
    # 创建新的会话
    session = Session()
    try:
        # Get cultivation records
        cultivation_records = get_cultivation_records()

        if not cultivation_records:
            st.info("目前没有栽培记录数据")
            return

        # Basic statistics
        total_cultivations = len(cultivation_records)
        active_cultivations = len([r for r in cultivation_records if r.status == "活"])
        flowering_cultivations = len([r for r in cultivation_records if r.flowering])
        fruiting_cultivations = len([r for r in cultivation_records if r.fruiting])
        dead_cultivations = len([r for r in cultivation_records if r.status == "死亡"])

        # Display basic statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("总栽培记录", total_cultivations)
        with col2:
            st.metric("存活植株", active_cultivations)
        with col3:
            st.metric("开花植株", flowering_cultivations)
        with col4:
            st.metric("结果植株", fruiting_cultivations)
        with col5:
            st.metric("死亡植株", dead_cultivations)

        # Prepare data for taxonomic statistics
        families = {}
        genera = {}

        for record in cultivation_records:
            # Get taxonomic info from the record or its related seed batch or collection
            family = record.family
            genus = record.genus

            if not family and record.seed_batch and record.seed_batch.collection:
                family = record.seed_batch.collection.family

            if not genus and record.seed_batch and record.seed_batch.collection:
                genus = record.seed_batch.collection.genus

            # Count by family
            if family:
                if family in families:
                    families[family] += 1
                else:
                    families[family] = 1

            # Count by genus
            if genus:
                if genus in genera:
                    genera[genus] += 1
                else:
                    genera[genus] = 1

        # Display taxonomic charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("按科统计")
            if families:
                # Sort and get top 10 families
                sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)[:10]
                family_names = [f[0] for f in sorted_families]
                family_counts = [f[1] for f in sorted_families]

                fig, ax = plt.subplots()
                ax.barh(family_names, family_counts)
                ax.set_xlabel('数量')
                ax.set_ylabel('科')
                ax.set_title('栽培植物科分布 (Top 10)')
                st.pyplot(fig)
            else:
                st.info("暂无科分布数据")

        with col2:
            st.subheader("按属统计")
            if genera:
                # Sort and get top 10 genera
                sorted_genera = sorted(genera.items(), key=lambda x: x[1], reverse=True)[:10]
                genus_names = [g[0] for g in sorted_genera]
                genus_counts = [g[1] for g in sorted_genera]

                fig, ax = plt.subplots()
                ax.barh(genus_names, genus_counts)
                ax.set_xlabel('数量')
                ax.set_ylabel('属')
                ax.set_title('栽培植物属分布 (Top 10)')
                st.pyplot(fig)
            else:
                st.info("暂无属分布数据")

        # Status change over time
        st.subheader("栽培状态随时间变化")

        # Get all cultivation events
        all_events = []
        for record in cultivation_records:
            events = get_cultivation_events(record.id)
            all_events.extend(events)

        if all_events:
            # Group events by month
            events_by_month = {}
            for event in all_events:
                month_key = event.event_date.strftime('%Y-%m')
                if month_key not in events_by_month:
                    events_by_month[month_key] = {
                        "浇水": 0, "施肥": 0, "修剪": 0, "观察": 0, "开花": 0, "结果": 0, "死亡": 0, "其他": 0
                    }

                event_type = event.event_type
                if event_type not in events_by_month[month_key]:
                    event_type = "其他"

                events_by_month[month_key][event_type] += 1

            # Sort months
            sorted_months = sorted(events_by_month.keys())

            # Prepare data for chart
            event_types = ["浇水", "施肥", "修剪", "观察", "开花", "结果", "死亡", "其他"]
            data = {
                "月份": sorted_months
            }

            for event_type in event_types:
                data[event_type] = [events_by_month[month][event_type] for month in sorted_months]

            # Create DataFrame
            df = pd.DataFrame(data)

            # Plot
            fig, ax = plt.subplots(figsize=(12, 6))
            bottom = np.zeros(len(sorted_months))

            for event_type in event_types:
                ax.bar(df["月份"], df[event_type], bottom=bottom, label=event_type)
                bottom += df[event_type].values

            ax.set_xlabel('月份')
            ax.set_ylabel('事件数量')
            ax.set_title('栽培事件随时间变化')
            ax.legend()

            # Rotate x-labels for better readability
            plt.xticks(rotation=45)

            st.pyplot(fig)
        else:
            st.info("暂无栽培事件数据")

        # Survival rate analysis
        st.subheader("存活率分析")

        # Get all completed cultivations (older than 3 months)
        three_months_ago = datetime.datetime.now().date() - datetime.timedelta(days=90)
        completed_cultivations = [r for r in cultivation_records if r.start_date < three_months_ago]

        if completed_cultivations:
            # Calculate survival rates by location
            locations = {}
            for record in completed_cultivations:
                if record.location not in locations:
                    locations[record.location] = {"total": 0, "alive": 0}

                locations[record.location]["total"] += 1
                if record.status == "活":
                    locations[record.location]["alive"] += 1

            # Calculate survival rates
            location_names = []
            survival_rates = []

            for location, counts in locations.items():
                if counts["total"] >= 5:  # Only include locations with at least 5 records
                    location_names.append(location)
                    survival_rates.append(counts["alive"] / counts["total"] * 100)

            if location_names:
                # Plot
                fig, ax = plt.subplots()
                ax.bar(location_names, survival_rates)
                ax.set_xlabel('栽培位置')
                ax.set_ylabel('存活率 (%)')
                ax.set_title('不同栽培位置的植物存活率')
                ax.set_ylim(0, 100)

                # Rotate x-labels for better readability
                plt.xticks(rotation=45)

                st.pyplot(fig)
            else:
                st.info("没有足够的数据进行位置存活率分析")
        else:
            st.info("暂无完成的栽培记录")
    finally:
        # 确保会话被关闭
        session.close()


def get_harvested_seeds(cultivation_id):
    """获取从栽培记录收获的种子批次"""
    session = Session()
    seeds = session.query(SeedBatch).filter(SeedBatch.parent_cultivation_id == cultivation_id).all()
    session.close()
    return seeds