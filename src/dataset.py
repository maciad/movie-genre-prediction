import torch


class MoviesDataset(torch.utils.data.Dataset):
	def __init__(self, encodings, labels):
		self.encodings = encodings
		self.labels = labels

	def __getitem__(self, idx):
		return {
			'input_ids': torch.tensor(self.encodings['input_ids'][idx], dtype=torch.long),
			'attention_mask': torch.tensor(self.encodings['attention_mask'][idx], dtype=torch.long),
			'labels': torch.tensor(self.labels[idx], dtype=torch.float)
		}
	
	def __len__(self):
		return len(self.labels)