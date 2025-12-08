import torch
from transformers import AutoModel


class HerBERTMultiLabelClassifier(torch.nn.Module):
	def __init__(self, num_labels: int, model_name: str="allegro/herbert-base-cased", dropout: float=0.25):
		super().__init__()
		self.encoder = AutoModel.from_pretrained(model_name)
		hidden_size = self.encoder.config.hidden_size

		self.classifier = torch.nn.Sequential(
			torch.nn.Dropout(dropout),
			torch.nn.Linear(hidden_size, hidden_size // 2),
			torch.nn.ReLU(),
			torch.nn.Dropout(dropout),
			torch.nn.Linear(hidden_size // 2, num_labels)
		)

	def forward(self, input_ids, attention_mask):
		outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
		cls_output = outputs.last_hidden_state[:, 0, :]  # CLS token output
		logits = self.classifier(cls_output)
		return logits
	
	def predict(self, input_ids, attention_mask, threshold=0.3, return_probs=False):
		logits = self.forward(input_ids, attention_mask)
		probs = torch.sigmoid(logits)
		preds = (probs >= threshold).float()
		if return_probs:
			return preds, probs
		return preds
	

class HerBERTFrozenMultiLabelClassifier(torch.nn.Module):
	def __init__(self, num_labels: int, model_name: str="allegro/herbert-base-cased", dropout: float=0.25):
		super().__init__()
		self.encoder =self.create_encoder(model_name)
		hidden_size = self.encoder.config.hidden_size

		self.classifier = torch.nn.Sequential(
			torch.nn.Dropout(dropout),
			torch.nn.Linear(hidden_size, hidden_size // 2),
			torch.nn.ReLU(),
			torch.nn.Dropout(dropout),
			torch.nn.Linear(hidden_size // 2, num_labels)
		)
		
	def create_encoder(self, model_name):
		encoder = AutoModel.from_pretrained(model_name)
		for param in encoder.parameters():
			param.requires_grad = False
		return encoder
    

	def forward(self, input_ids, attention_mask):
		outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
		cls_output = outputs.last_hidden_state[:, 0, :]  # CLS token output
		logits = self.classifier(cls_output)
		return logits
	
	def predict(self, input_ids, attention_mask, threshold=0.3, return_probs=False):
		logits = self.forward(input_ids, attention_mask)
		probs = torch.sigmoid(logits)
		preds = (probs >= threshold).float()
		if return_probs:
			return preds, probs
		return preds