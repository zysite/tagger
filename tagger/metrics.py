# -*- coding: utf-8 -*-

import torch


class Metric(object):

    def __lt__(self, other):
        return self.score < other

    def __le__(self, other):
        return self.score <= other

    def __eq__(self, other):
        return self.score == other

    def __ge__(self, other):
        return self.score >= other

    def __gt__(self, other):
        return self.score > other

    def __ne__(self, other):
        return self.score != other

    @property
    def score(self):
        raise AttributeError


class AccuracyMethod(Metric):

    def __init__(self, eps=1e-5):
        super(AccuracyMethod, self).__init__()

        self.tp = 0.0
        self.total = 0.0
        self.eps = eps

    def __call__(self, preds, golds):
        for pred, gold in zip(preds, golds):
            self.tp += torch.sum(pred == gold).item()
            self.total += len(gold)

    def __repr__(self):
        return f"Accuracy: {self.accuracy:.2%}"

    @property
    def score(self):
        return self.accuracy

    @property
    def accuracy(self):
        return self.tp / (self.total + self.eps)


class SpanF1Method(Metric):

    def __init__(self, vocab, eps=1e-5):
        super(SpanF1Method, self).__init__()

        self.tp = 0.0
        self.pred = 0.0
        self.gold = 0.0
        self.vocab = vocab
        self.eps = eps

    def __call__(self, preds, golds):
        for pred, gold in zip(preds, golds):
            pred_spans = self.get_entities(pred)
            gold_spans = self.get_entities(gold)
            self.tp += len(pred_spans & gold_spans)
            self.pred += len(pred_spans)
            self.gold += len(gold_spans)

    def __repr__(self):
        p, r, f = self.precision, self.recall, self.f_score

        return f"Precision: {p:.2%} Recall: {r:.2%} F: {f:.2%}"

    @property
    def score(self):
        return self.f_score

    @property
    def precision(self):
        return self.tp / (self.pred + self.eps)

    @property
    def recall(self):
        return self.tp / (self.gold + self.eps)

    @property
    def f_score(self):
        precision = self.precision
        recall = self.recall

        return 2 * precision * recall / (precision + recall + self.eps)

    def get_entities(self, ids):
        span, chunks = [], []

        for i, tag in enumerate(self.vocab.id_to_tag(ids)):
            if tag == 'O':
                stype = 'O'
            else:
                stype, etype = tag.split('-')
            if stype == 'B':
                if span:
                    chunks.append(tuple(span))
                span = [etype, i, 1]
            elif stype == 'S':
                if span:
                    chunks.append(tuple(span))
                    span.clear()
                chunks.append((etype, i, 1))
            elif stype == 'I':
                if span:
                    if etype == span[0]:
                        span[-1] += 1
                    else:
                        chunks.append(tuple(span))
                        span = [etype, i, 1]
                else:
                    span = [etype, i, 1]
            elif stype == 'E':
                if span:
                    if etype == span[0]:
                        span[-1] += 1
                        chunks.append(tuple(span))
                        span.clear()
                    else:
                        chunks.append(tuple(span))
                        span.clear()
                        chunks.append((etype, i, 1))
                else:
                    chunks.append((etype, i, 1))
                    span.clear()
            else:
                if span:
                    chunks.append(tuple(span))
                span.clear()
        if span:
            chunks.append(tuple(span))

        return set(chunks)
