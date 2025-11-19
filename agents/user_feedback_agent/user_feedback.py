"""
User Feedback Agent
===================
Captura avaliações do usuário sobre as respostas fornecidas pelo sistema.

Este agente NÃO usa IA/GPT - apenas registra o feedback estruturado do usuário.

Inputs esperados no state:
    - pergunta: str (pergunta original do usuário)
    - username: str
    - projeto: str
    - response_text: str (resposta que foi apresentada ao usuário)
    - rating: int (1-5 estrelas)
    - comment: str (comentário opcional do usuário)
    - is_helpful: bool (se a resposta foi útil)
    - response_quality: str (poor/fair/good/excellent)
    - user_satisfaction: str (unsatisfied/neutral/satisfied/very_satisfied)
    - would_recommend: bool (se recomendaria o sistema)
    - feedback_tags: List[str] (tags: accurate, fast, clear, incomplete, wrong, etc)

Outputs:
    - feedback_recorded: bool
    - feedback_summary: str
    - improvement_areas: List[str] (áreas que precisam melhorar)
    - positive_aspects: List[str] (aspectos positivos mencionados)
"""

import json
from datetime import datetime
from typing import Dict, Any, List


class UserFeedbackAgent:
    """Agente que processa e estrutura feedback do usuário"""
    
    def __init__(self):
        """Inicializar agente de feedback"""
        print("[USER_FEEDBACK_AGENT] 🎯 Agente de feedback inicializado")
        
        # Mapeamento de tags para categorias
        self.positive_tags = {'accurate', 'fast', 'clear', 'helpful', 'complete', 'easy_to_understand'}
        self.negative_tags = {'incomplete', 'wrong', 'slow', 'confusing', 'unclear', 'not_helpful'}
        
        # Mapeamento de rating para qualidade
        self.rating_to_quality = {
            1: 'poor',
            2: 'fair',
            3: 'good',
            4: 'very_good',
            5: 'excellent'
        }
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processar e estruturar feedback do usuário
        
        Args:
            state: Estado contendo feedback do usuário
            
        Returns:
            Dict com feedback estruturado e análise
        """
        try:
            print(f"[USER_FEEDBACK_AGENT] 📝 Processando feedback do usuário...")
            print(f"[USER_FEEDBACK_AGENT]    Username: {state.get('username')}")
            print(f"[USER_FEEDBACK_AGENT]    Projeto: {state.get('projeto')}")
            print(f"[USER_FEEDBACK_AGENT]    Rating: {state.get('rating')}/5")
            
            # Extrair dados do feedback
            rating = state.get('rating', 0)
            comment = state.get('comment', '')
            is_helpful = state.get('is_helpful', False)
            response_quality = state.get('response_quality', '')
            user_satisfaction = state.get('user_satisfaction', '')
            would_recommend = state.get('would_recommend', False)
            feedback_tags = state.get('feedback_tags', [])
            
            # Validar rating
            if not (1 <= rating <= 5):
                print(f"[USER_FEEDBACK_AGENT] ⚠️  Rating inválido: {rating}. Usando 0.")
                rating = 0
            
            # Inferir response_quality se não fornecido
            if not response_quality and rating > 0:
                response_quality = self.rating_to_quality.get(rating, 'fair')
            
            # Analisar tags
            positive_aspects = [tag for tag in feedback_tags if tag in self.positive_tags]
            improvement_areas = [tag for tag in feedback_tags if tag in self.negative_tags]
            
            # Gerar resumo do feedback
            feedback_summary = self._generate_summary(
                rating, is_helpful, response_quality, 
                user_satisfaction, would_recommend, comment
            )
            
            # Identificar sentiment
            sentiment = self._calculate_sentiment(rating, is_helpful, would_recommend)
            
            print(f"[USER_FEEDBACK_AGENT] ✅ Feedback processado")
            print(f"[USER_FEEDBACK_AGENT]    Útil: {is_helpful}")
            print(f"[USER_FEEDBACK_AGENT]    Qualidade: {response_quality}")
            print(f"[USER_FEEDBACK_AGENT]    Satisfação: {user_satisfaction}")
            print(f"[USER_FEEDBACK_AGENT]    Sentiment: {sentiment}")
            print(f"[USER_FEEDBACK_AGENT]    Aspectos positivos: {len(positive_aspects)}")
            print(f"[USER_FEEDBACK_AGENT]    Áreas de melhoria: {len(improvement_areas)}")
            
            # Retornar feedback estruturado
            return {
                'feedback_recorded': True,
                'rating': rating,
                'comment': comment,
                'is_helpful': is_helpful,
                'response_quality': response_quality,
                'user_satisfaction': user_satisfaction,
                'would_recommend': would_recommend,
                'feedback_tags': feedback_tags,
                'feedback_summary': feedback_summary,
                'positive_aspects': positive_aspects,
                'improvement_areas': improvement_areas,
                'sentiment': sentiment,
                'feedback_date': datetime.now().isoformat(),
                'error': None
            }
            
        except Exception as e:
            print(f"[USER_FEEDBACK_AGENT] ❌ Erro ao processar feedback: {e}")
            return {
                'feedback_recorded': False,
                'rating': 0,
                'comment': '',
                'is_helpful': False,
                'response_quality': 'unknown',
                'user_satisfaction': 'unknown',
                'would_recommend': False,
                'feedback_tags': [],
                'feedback_summary': '',
                'positive_aspects': [],
                'improvement_areas': [],
                'sentiment': 'neutral',
                'feedback_date': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _generate_summary(
        self, 
        rating: int, 
        is_helpful: bool, 
        response_quality: str,
        user_satisfaction: str,
        would_recommend: bool,
        comment: str
    ) -> str:
        """Gerar resumo textual do feedback"""
        
        parts = []
        
        # Rating
        if rating > 0:
            parts.append(f"Avaliação: {rating}/5 estrelas")
        
        # Helpful
        parts.append(f"Útil: {'Sim' if is_helpful else 'Não'}")
        
        # Quality
        if response_quality:
            quality_map = {
                'poor': 'Ruim',
                'fair': 'Razoável',
                'good': 'Boa',
                'very_good': 'Muito Boa',
                'excellent': 'Excelente'
            }
            parts.append(f"Qualidade: {quality_map.get(response_quality, response_quality)}")
        
        # Satisfaction
        if user_satisfaction:
            satisfaction_map = {
                'unsatisfied': 'Insatisfeito',
                'neutral': 'Neutro',
                'satisfied': 'Satisfeito',
                'very_satisfied': 'Muito Satisfeito'
            }
            parts.append(f"Satisfação: {satisfaction_map.get(user_satisfaction, user_satisfaction)}")
        
        # Recommendation
        if would_recommend:
            parts.append("Recomendaria o sistema")
        
        # Comment
        if comment:
            parts.append(f"Comentário: {comment[:100]}")
        
        return " | ".join(parts)
    
    def _calculate_sentiment(self, rating: int, is_helpful: bool, would_recommend: bool) -> str:
        """Calcular sentiment geral do feedback"""
        
        score = 0
        
        # Rating contribui mais
        if rating >= 4:
            score += 3
        elif rating == 3:
            score += 1
        elif rating <= 2 and rating > 0:
            score -= 2
        
        # Helpful
        if is_helpful:
            score += 2
        else:
            score -= 1
        
        # Recommendation
        if would_recommend:
            score += 2
        else:
            score -= 1
        
        # Classificar sentiment
        if score >= 5:
            return 'very_positive'
        elif score >= 2:
            return 'positive'
        elif score >= -1:
            return 'neutral'
        elif score >= -3:
            return 'negative'
        else:
            return 'very_negative'


if __name__ == '__main__':
    # Teste básico
    agent = UserFeedbackAgent()
    
    test_state = {
        'pergunta': 'Quantas vendas tivemos hoje?',
        'username': 'test_user',
        'projeto': 'vendas',
        'response_text': 'Hoje foram registradas 245 vendas...',
        'rating': 5,
        'comment': 'Resposta muito clara e completa!',
        'is_helpful': True,
        'response_quality': 'excellent',
        'user_satisfaction': 'very_satisfied',
        'would_recommend': True,
        'feedback_tags': ['accurate', 'fast', 'clear', 'helpful']
    }
    
    result = agent.execute(test_state)
    print("\n" + "="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
