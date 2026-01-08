"""
文章总结生成器
用于生成每日和每周的文章总结
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.app.db import DatabaseManager
from backend.app.db.models import Article, DailySummary
from backend.app.services.analyzer.ai_analyzer import AIAnalyzer
import logging

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """文章总结生成器"""

    def __init__(self, ai_analyzer: AIAnalyzer):
        self.ai_analyzer = ai_analyzer

    def generate_daily_summary(self, db: DatabaseManager, date: datetime = None) -> DailySummary:
        """
        生成每日总结

        Args:
            db: 数据库管理器
            date: 总结日期（默认今天），会计算该日期当天的00:00:00至23:59:59

        Returns:
            DailySummary对象
        """
        if date is None:
            date = datetime.now()

        # 计算该天的起始和结束时间
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"📝 生成每日总结: {start_date.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_date.strftime('%Y-%m-%d %H:%M:%S')}")

        # 直接在同一个session中处理所有逻辑
        return self._create_summary(db, start_date, end_date, "daily", date)

    def generate_weekly_summary(self, db: DatabaseManager, date: datetime = None) -> DailySummary:
        """
        生成每周总结

        Args:
            db: 数据库管理器
            date: 总结日期（默认今天），会计算该日期所在自定义周的周六至周五
            自定义周规则：周六、周日、周一到周五，为一个总结周

        Returns:
            DailySummary对象
        """
        if date is None:
            date = datetime.now()

        # 使用自定义周标准计算该周的起始日期（周六）和结束日期（周五）
        # 自定义周：周六到周五，weekday(): Monday=0, Sunday=6
        # 需要找到该日期所在周的周六（起始）和周五（结束）
        weekday = date.weekday()  # Monday=0, Tuesday=1, ..., Sunday=6
        
        # 计算距离上周六的天数
        # 如果今天是周六(5)，则距离上周六是0天
        # 如果今天是周日(6)，则距离上周六是1天
        # 如果今天是周一(0)，则距离上周六是2天
        # 如果今天是周五(4)，则距离上周六是6天
        if weekday == 5:  # 周六
            days_since_saturday = 0
        elif weekday == 6:  # 周日
            days_since_saturday = 1
        else:  # 周一到周五
            days_since_saturday = weekday + 2
        
        start_date = date - timedelta(days=days_since_saturday)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 结束日期是周五（起始日期+6天）
        end_date = start_date + timedelta(days=6)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"📝 生成每周总结: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 使用该周的周五作为summary_date
        summary_date = end_date

        # 直接在同一个session中处理所有逻辑
        return self._create_summary(db, start_date, end_date, "weekly", summary_date)

    def _create_summary(
        self,
        db: DatabaseManager,
        start_date: datetime,
        end_date: datetime,
        summary_type: str,
        date: datetime
    ) -> DailySummary:
        """
        创建总结

        Args:
            db: 数据库管理器
            start_date: 开始时间
            end_date: 结束时间
            summary_type: 总结类型（daily/weekly）
            date: 总结日期

        Returns:
            DailySummary对象
        """
        start_time = datetime.now()

        # 在同一个session中查询文章并提取数据
        with db.get_session() as session:
            # 查询已分析的文章，按重要性和发布时间排序
            articles = session.query(Article).filter(
                Article.is_processed == True,
                Article.published_at >= start_date,
                Article.published_at <= end_date
            ).order_by(
                Article.importance.desc(),
                Article.published_at.desc()
            ).all()

            if not articles:
                logger.warning("⚠️  没有找到符合条件的文章")
                return None

            # 准备文章数据
            articles_data = []
            for article in articles:
                display_title = article.title_zh if article.title_zh else article.title
                articles_data.append({
                    "id": article.id,
                    "title": display_title,
                    "source": article.source,
                    "importance": article.importance,
                    "published_at": article.published_at,
                    "summary": article.summary,
                })

        # 统计信息
        high_count = sum(1 for a in articles_data if a.get("importance") == "high")
        medium_count = sum(1 for a in articles_data if a.get("importance") == "medium")

        logger.info(f"  文章总数: {len(articles_data)} (高重要性: {high_count}, 中重要性: {medium_count})")

        # 调用LLM生成总结
        prompt = self._build_summary_prompt(articles_data, summary_type, start_date, end_date)
        
        # 根据总结类型设置不同的系统提示词和参数
        if summary_type == "weekly":
            # 周报使用专业的行业分析师角色和更高的参数
            system_prompt = """你是一名资深的行业分析师和风向洞察者，拥有超过15年的从业经验。你不仅关注新闻事件的表面，更擅长从纷繁复杂的信息中，穿透表象，识别出那些真正能够影响行业格局的潜在变化、新兴趋势和关键信号。你的分析以深刻、前瞻和高度概括性著称，旨在为决策者提供高价值的参考。

请使用Markdown格式输出所有内容，包括标题、列表、加粗等Markdown语法。"""
            temperature = 0.5  # 周报需要更多创造性分析
            max_tokens = 4000  # 周报需要更详细的分析
        else:
            # 日报使用原有的系统提示词
            system_prompt = "你是一个专业的AI领域新闻分析助手，擅长从大量文章中提炼关键信息和趋势。请使用Markdown格式输出所有内容，包括标题、列表、加粗等Markdown语法。"
            temperature = 0.3
            max_tokens = 2000
        
        summary_content = self.ai_analyzer.client.chat.completions.create(
            model=self.ai_analyzer.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        summary_text = summary_content.choices[0].message.content

        # 提取关键主题
        key_topics = self._extract_topics(articles_data)

        # 推荐重要文章
        recommended_articles = self._select_recommended_articles(articles_data)

        # 计算耗时
        generation_time = (datetime.now() - start_time).total_seconds()

        # 保存到数据库（如果已存在则更新，否则创建）
        with db.get_session() as session:
            # 检查是否已存在相同类型和日期的总结
            # 对于daily类型，比较日期（忽略时间部分）
            # 对于weekly类型，比较summary_date所在的周
            existing_summary = None
            if summary_type == "daily":
                # 每日总结：比较日期（只比较年月日）
                date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
                existing_summary = session.query(DailySummary).filter(
                    DailySummary.summary_type == summary_type,
                    DailySummary.summary_date >= date_only,
                    DailySummary.summary_date < date_only + timedelta(days=1)
                ).first()
            else:
                # 每周总结：比较summary_date所在的自定义周（周六到周五）
                # 计算summary_date所在周的周六和周五
                weekday = date.weekday()
                if weekday == 5:  # 周六
                    days_since_saturday = 0
                elif weekday == 6:  # 周日
                    days_since_saturday = 1
                else:  # 周一到周五
                    days_since_saturday = weekday + 2
                
                week_start = date - timedelta(days=days_since_saturday)
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                week_end = week_start + timedelta(days=7)
                
                existing_summary = session.query(DailySummary).filter(
                    DailySummary.summary_type == summary_type,
                    DailySummary.summary_date >= week_start,
                    DailySummary.summary_date < week_end
                ).first()
            
            if existing_summary:
                # 更新现有总结
                existing_summary.start_date = start_date
                existing_summary.end_date = end_date
                existing_summary.total_articles = len(articles_data)
                existing_summary.high_importance_count = high_count
                existing_summary.medium_importance_count = medium_count
                existing_summary.summary_content = summary_text
                existing_summary.key_topics = key_topics
                existing_summary.recommended_articles = recommended_articles
                existing_summary.model_used = self.ai_analyzer.model
                existing_summary.generation_time = generation_time
                existing_summary.updated_at = datetime.now()
                session.flush()
                summary_id = existing_summary.id
                logger.info(f"✅ 总结已更新 (ID: {summary_id})")
            else:
                # 创建新总结
                summary = DailySummary(
                    summary_type=summary_type,
                    summary_date=date,
                    start_date=start_date,
                    end_date=end_date,
                    total_articles=len(articles_data),
                    high_importance_count=high_count,
                    medium_importance_count=medium_count,
                    summary_content=summary_text,
                    key_topics=key_topics,
                    recommended_articles=recommended_articles,
                    model_used=self.ai_analyzer.model,
                    generation_time=generation_time
                )
                session.add(summary)
                session.flush()
                summary_id = summary.id
                logger.info(f"✅ 总结已保存 (ID: {summary_id})")
            
        # 在session外创建一个新的对象返回，避免detached instance问题
        return DailySummary(
            id=summary_id,
            summary_type=summary_type,
            summary_date=date,
            start_date=start_date,
            end_date=end_date,
            total_articles=len(articles_data),
            high_importance_count=high_count,
            medium_importance_count=medium_count,
            summary_content=summary_text,
            key_topics=key_topics,
            recommended_articles=recommended_articles,
            model_used=self.ai_analyzer.model,
            generation_time=generation_time
        )

    def _build_summary_prompt(
        self, 
        articles_data: List[Dict[str, Any]], 
        summary_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """
        构建总结提示词

        Args:
            articles_data: 文章数据列表
            summary_type: 总结类型（daily/weekly）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            提示词字符串
        """
        # 根据日期范围生成具体的时间描述
        if summary_type == "daily":
            # 每日总结：显示具体日期
            time_str = start_date.strftime('%Y年%m月%d日')
        else:
            # 每周总结：显示日期范围
            time_str = f"{start_date.strftime('%Y年%m月%d日')} 至 {end_date.strftime('%Y年%m月%d日')}"
            date_range = f"{start_date.strftime('%Y年%m月%d日')} 至 {end_date.strftime('%Y年%m月%d日')}"

        # 选择最重要的文章（周报使用更多文章，日报保持原样）
        if summary_type == "weekly":
            important_articles = articles_data[:50]  # 周报使用更多文章进行分析
        else:
            important_articles = articles_data[:20]

        # 构建文章列表
        articles_str = ""
        for i, article in enumerate(important_articles, 1):
            importance_emoji = "🔴" if article.get("importance") == "high" else "🟡" if article.get("importance") == "medium" else "⚪"
            # 周报需要更详细的信息
            if summary_type == "weekly":
                articles_str += f"""
{i}. {importance_emoji} [{article.get('source', 'Unknown')}] {article.get('title', 'N/A')}
   发布时间: {article.get('published_at', datetime.now()).strftime('%Y-%m-%d %H:%M')}
   摘要: {article.get('summary', '')[:300]}
"""
            else:
                articles_str += f"""
{i}. {importance_emoji} [{article.get('source', 'Unknown')}] {article.get('title', 'N/A')}
   发布时间: {article.get('published_at', datetime.now()).strftime('%Y-%m-%d %H:%M')}
   摘要: {article.get('summary', '')[:200]}...
"""

        # 根据类型生成不同的提示词
        if summary_type == "weekly":
            # 周报使用专业的行业风向洞察提示词
            prompt = f"""# 任务 (Mission)

基于我本周提供的（人工智能/AI）行业相关新闻资讯，产出一份专业的《本周行业风向洞察摘要》。你的报告需要超越简单的信息罗列，核心在于**提炼观点、解读趋势、并预测其潜在影响**。

# 工作流程 (Workflow)

1. **信息梳理与聚合**：首先，全面阅读并理解我提供的所有新闻内容。将相关联的事件、数据和观点进行分类聚合。
2. **关键主题识别**：从聚合后的信息中，识别出本周反复出现或最重要的2-3个核心主题或关键变量。这些是变化的源头。
3. **趋势提炼与命名**：基于这些核心主题，提炼出本周最值得关注的行业趋势。为每个趋势赋予一个精准且概括性强的标题（例如："AI大模型应用加速落地"、"市场转向追求性价比消费"、"供应链区域化趋势凸显"等）。
4. **深度分析与解读**：
   * **"发生了什么？"**：简要说明该趋势由哪些具体新闻事件支撑。
   * **"这意味着什么？"**：深入分析这些事件背后反映出的行业变化。是技术突破？是消费者行为变迁？是政策驱动？还是资本流向的改变？
   * **"将带来什么影响？"**：从短期和中长期两个维度，预测这一趋势可能对行业生态、竞争格局、产业链上下游以及相关企业带来的潜在影响、机遇或挑战。
5. **总结与展望**：在报告的最后，用一段话对本周的整体行业动态进行总结，并对未来1-3个月的动向给出一个简要的展望或需要关注的焦点。

# 输出格式 (Output Format)

请严格按照以下结构化格式输出你的报告，以确保专业性和可读性：

---

**【人工智能行业风向洞察周报 | {date_range}】**

**一、 本周核心摘要 (Executive Summary)**
*   （用2-3句话高度概括本周最重要的行业变化和核心观点，让读者能迅速把握要点。）

**二、 本周关键趋势洞察 (Key Trends Insight)**

*   **趋势一：[为趋势一命名]**
    *   **现象描述**：由本周的[新闻事件A]、[数据B]等共同指向...
    *   **趋势解读**：这反映出行业在[某个方面]正在发生深刻转变，其核心驱动力是...
    *   **潜在影响与机遇**：短期来看，这将对[相关企业/领域]带来...机会/挑战。长期来看，我们预测...

*   **趋势二：[为趋势二命名]**
    *   **现象描述**：本周[公司C的动态]与[政策D的出台]...
    *   **趋势解读**：这标志着市场竞争的焦点正从...转向...，背后的逻辑是...
    *   **潜在影响与机遇**：这将迫使企业重新思考其...战略。对于[特定类型的公司]而言，这可能是一个...的窗口期。

*   **（可选）趋势三：[为趋势三命名]**
    *   ...

**三、 未来展望 (Future Outlook)**
*   （综合本周观察，我们判断未来几周内，行业需要密切关注...。特别是...方面的动向，可能会成为下一个引爆点。）

---

# 关键要求 (Key Requirements)

*   **拒绝罗列**：不要简单地复述新闻，必须进行提炼和升华。
*   **观点鲜明**：在分析和解读部分，要敢于提出你基于信息的判断和观点。
*   **逻辑清晰**：确保现象、解读和影响之间的逻辑链条是清晰且有说服力的。
*   **语言专业**：使用专业、精炼、客观的商业分析语言。

# 本周新闻素材 (Weekly News Input)

以下是本周收集到的所有新闻标题、摘要和关键信息：

{articles_str}

请基于以上新闻素材，按照上述格式和要求，生成专业的《人工智能行业风向洞察周报》。"""
        else:
            # 日报保持原有格式
            prompt = f"""请基于{time_str}期间采集的以下AI领域文章，生成一份{time_str}的新闻总结。

文章列表：
{articles_str}

请使用Markdown格式输出总结，按以下格式：

# 📊 {time_str}AI新闻总结

## 🔥 重点文章
列出3-5篇最重要的文章，每篇文章格式如下：
- **文章标题（来源）**：直接描述文章的核心内容和重要性，不要使用"核心内容"、"为什么重要"、"文章标题和来源"等任何标签或子标题，直接输出内容即可。例如：
  - **能文能武!智元首个机器人艺人天团亮相湖南卫视跨年演唱会（量子位）**
    智元机器人首次在大型电视节目中亮相，展示了AI机器人在娱乐领域的应用潜力，标志着机器人从工业场景向消费场景的重要突破。

## 📌 重要趋势
从这些文章中总结出2-3个重要趋势或热点话题

## 🎯 推荐阅读
根据文章的关联性和重要性，推荐5-10篇值得深入阅读的文章

**重要提示：请确保输出内容使用标准的Markdown格式，包括标题（#、##）、列表（-、*）、加粗（**文本**）等Markdown语法。请用中文回答，保持专业、简洁的风格。"""

        return prompt

    def _extract_topics(self, articles_data: List[Dict[str, Any]]) -> List[str]:
        """
        从文章中提取关键主题（从摘要中提取）

        Args:
            articles_data: 文章数据列表

        Returns:
            主题列表（空列表，因为不再从topics字段提取）
        """
        # 不再从topics字段提取，返回空列表
        return []

    def _select_recommended_articles(self, articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        选择推荐文章

        Args:
            articles_data: 文章数据列表

        Returns:
            推荐文章列表
        """
        recommended = []

        # 优先选择高重要性文章
        high_importance = [a for a in articles_data if a.get("importance") == "high"]
        medium_importance = [a for a in articles_data if a.get("importance") == "medium"]

        # 选择最多10篇推荐文章
        selected_articles = (high_importance + medium_importance)[:10]

        for article in selected_articles:
            reason = ""
            if article.get("importance") == "high":
                reason = "高重要性文章，值得重点关注"
            elif article.get("importance") == "medium":
                reason = "中等重要性，建议阅读"

            recommended.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "source": article.get("source"),
                "importance": article.get("importance"),
                "reason": reason
            })

        return recommended
