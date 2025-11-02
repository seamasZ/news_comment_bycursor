import csv
import io
from database.crud import get_record_by_id


class CSVExporter:
    """CSV导出器"""
    
    def export_record(self, record_id: int) -> str:
        """导出单条记录的评论为CSV"""
        record = get_record_by_id(record_id)
        
        if not record:
            raise ValueError(f"记录 {record_id} 不存在")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(["ID", "评论内容", "语言风格", "观点倾向"])
        
        # 写入评论数据
        comments = record.get("comments", [])
        for idx, comment in enumerate(comments, 1):
            writer.writerow([
                idx,
                comment.get("text", ""),
                comment.get("style", ""),
                comment.get("perspective", "")
            ])
        
        return output.getvalue()



