import pathlib
import re


class ipa2Kana:

    def __init__(self):

        self.vowels = {
            'AA': '',  # 曖昧
            'AH': '',  # 曖昧
            'AE': 'a',
            'AO': 'o',
            'AW': 'a',
            'AY': 'a',
            'EH': 'e',
            'ER': 'a',
            'EY': 'e',
            'IH': 'i',
            'IY': 'i',
            'OW': 'o',
            'OY': 'o',
            'UH': 'u',
            'UW': 'u',
        }

        self.kana_dic = {
            # be	B IY
            'B': {'a': 'バ', 'i': 'ビ', 'u': 'ブ', 'e': 'ベ', 'o': 'ボ', '': 'ブ'},
            # cheese	CH IY Z#チch
            'CH': {'a': 'チャ', 'i': 'チ', 'u': 'チュ', 'e': 'チェ', 'o': 'チョ', '': 'チ'},
            # dee	D IY
            'D': {'a': 'ダ', 'i': 'ディ', 'u': 'ドゥ', 'e': 'デ', 'o': 'ド', '': 'ド'},
            # thee	DH IY
            'DH': {'a': 'ザ', 'i': 'ジ', 'u': 'ズ', 'e': 'ゼ', 'o': 'ゾ', '': 'ズ'},
            # fee	F IY
            'F': {'a': 'ファ', 'i': 'フィ', 'u': 'フ', 'e': 'フェ', 'o': 'フォ', '': 'フ'},
            # green	G R IY N
            'G': {'a': 'ガ', 'i': 'ギ', 'u': 'グ', 'e': 'ゲ', 'o': 'ゴ', '': 'グ'},
            # he	HH IY#H
            'HH': {'a': 'ハ', 'i': 'ヒ', 'u': 'フ', 'e': 'ヘ', 'o': 'ホ', '': 'フ'},
            # gee	JH IY#J
            'JH': {'a': 'ジャ', 'i': 'ジ', 'u': 'ジュ', 'e': 'ジェ', 'o': 'ジョ', '': 'ジ'},
            # key	K IY
            'K': {'a': 'カ', 'i': 'キ', 'u': 'ク', 'e': 'ケ', 'o': 'コ', '': 'ク'},
            # lee	L IY
            'L': {'a': 'ラ', 'i': 'リ', 'u': 'ル', 'e': 'レ', 'o': 'ロ', '': 'ル'},
            # me	M IY
            'M': {'a': 'マ', 'i': 'ミ', 'u': 'ム', 'e': 'メ', 'o': 'モ', '': 'ム'},
            # knee	N IY
            'N': {'a': 'ナ', 'i': 'ニ', 'u': 'ヌ', 'e': 'ネ', 'o': 'ノ', '': 'ン'},
            # ping	P IH NG
            'NG': {'a': 'ンガ', 'i': 'ンギ', 'u': 'ング', 'e': 'ンゲ', 'o': 'ンゴ', '': 'ング'},
            # pee	P IY
            'P': {'a': 'パ', 'i': 'ピ', 'u': 'プ', 'e': 'ペ', 'o': 'ポ', '': 'プ'},
            # read	R IY D
            'R': {'a': 'ラ', 'i': 'リ', 'u': 'ル', 'e': 'レ', 'o': 'ロ', '': 'ー'},
            # sea	S IY
            'S': {'a': 'サ', 'i': 'シ', 'u': 'ス', 'e': 'セ', 'o': 'ソ', '': 'ス'},
            # she	SH IY
            'SH': {'a': 'シャ', 'i': 'シ', 'u': 'シュ', 'e': 'シェ', 'o': 'ショ', '': 'シュ'},
            # tea	T IY
            'T': {'a': 'タ', 'i': 'ティ', 'u': 'チュ', 'e': 'テ', 'o': 'ト', '': 'ト'},
            # theta	TH EY T AH
            'TH': {'a': 'サ', 'i': 'シ', 'u': 'シュ', 'e': 'セ', 'o': 'ソ', '': 'ス'},
            # vee	V IY
            'V': {'a': 'バ', 'i': 'ビ', 'u': 'ブ', 'e': 'ベ', 'o': 'ボ', '': 'ブ'},
            # we	W IY
            'W': {'a': 'ワ', 'i': 'ウィ', 'u': 'ウ', 'e': 'ウェ', 'o': 'ウォ', '': 'ウ'},
            # yield	Y IY L D
            'Y': {'a': 'ア', 'i': '', 'u': 'ュ', 'e': 'エ', 'o': 'ョ', '': 'イ'},
            'BOS_Y': {'a': 'ヤ', 'i': 'イ', 'u': 'ユ', 'e': 'イエ', 'o': 'ヨ', '': 'イ'},
            # zee	Z IY
            'Z': {'a': 'ザ', 'i': 'ジ', 'u': 'ズ', 'e': 'ゼ', 'o': 'ゾ', '': 'ズ'},
            # seizure	S IY ZH ER
            'ZH': {'a': 'ジャ', 'i': 'ジ', 'u': 'ジュ', 'e': 'ジェ', 'o': 'ジョ', '': 'ジュ'},
            'T_S': {'a': 'ツァ', 'i': 'ツィ', 'u': 'ツ', 'e': 'ツェ', 'o': 'ツォ', '': 'ツ'},
        }

        # 変換用辞書
        self.eng_kana_dic = {}

    def convert(self, phonetic_alphabet: str) -> str:
        """
        英語文字列をカタカナに変換する
        """

        if phonetic_alphabet is not str:
            raise TypeError(
                f"'phonetic_alphabet' must be str but got type '{type(phonetic_alphabet)}'")

        sound_list = phonetic_alphabet.split(' ')
        yomi = ''

        # EOS と BOS　をつけておく
        sound_list = ['BOS'] + sound_list + ['EOS']
        for i in range(1, len(sound_list) - 1):

            s = sound_list[i]
            s_prev = sound_list[i - 1]
            s_next = sound_list[i + 1]

            if s_prev == 'BOS' and s == 'Y':
                # 頭がYの場合特殊
                s = sound_list[i] = 'BOS_Y'

            if s in self.kana_dic and s_next not in self.vowels:
                # 子音(→子音）
                if s_next in {'Y'}:
                    # 後ろが Y の場合イ行に
                    # ただし2文字の場合は2文字目を削る　例）フィ→フ
                    yomi += self.kana_dic[s]['i'][0]
                elif s == 'D' and s_next == 'Z':
                    # D音をスキップ
                    continue
                elif s == 'T' and s_next == 'S':
                    # 連結して'T_S'に
                    sound_list[i + 1] = 'T_S'
                    continue
                elif s == 'NG' and s_next in {'K', 'G'}:
                    # 'NG'の次が 'G' or 'K' の場合2文字目を削る　例）ング→ン
                    yomi += self.kana_dic[s][''][0]
                elif s_prev in {'EH', 'EY', 'IH', 'IY'} and s == 'R':
                    yomi += 'アー'
                else:
                    yomi += self.kana_dic[s]['']
            elif s in self.vowels:
                # 母音
                # aiueoに割り振る
                if s in {'AA', 'AH'}:
                    # 曖昧母音
                    # v = self.find_vowel(word, i - 1, len(sound_list) - 2) # わからんので飛ばす！
                    v = ""
                    pass
                else:
                    v = self.vowels[s]

                if s_prev in self.kana_dic:
                    # (子音→)母音で
                    # print(s,v)
                    yomi += self.kana_dic[s_prev][v]
                else:
                    # (母音→)母音
                    # 母音が連続すると変化するもの
                    if s_prev in {'AY', 'EY', 'OY'} and s not in {'AA', 'AH'}:  # 曖昧母音の場合は除外
                        yomi += {'a': 'ヤ', 'i': 'イ',
                                 'u': 'ユ', 'e': 'エ', 'o': 'ヨ'}[v]
                    elif s_prev in {'AW', 'UW'}:
                        yomi += {'a': 'ワ', 'i': 'ウィ',
                                 'u': 'ウ', 'e': 'ウェ', 'o': 'ウォ'}[v]
                    elif s_prev in {'ER'}:
                        yomi += {'a': 'ラ', 'i': 'リ',
                                 'u': 'ル', 'e': 'レ', 'o': 'ロ'}[v]
                    else:
                        # 変化しない
                        yomi += {'a': 'ア', 'i': 'イ',
                                 'u': 'ウ', 'e': 'エ', 'o': 'オ'}[v]

                # Yを母音化
                if s in {'AY', 'EY', 'OY'}:  # これは常に入れてOK?
                    yomi += 'イ'
                # 後続が母音かどうかで変化するもの
                if s_next not in self.vowels:
                    # 母音(→子音)
                    if s in {'ER', 'IY', 'OW', 'UW'}:
                        yomi += 'ー'
                    elif s in {'AW'}:
                        yomi += 'ウ'

        return yomi

    # 表記から母音を取り出す関数（曖昧母音用）
    def find_vowel(self, text, pos, length):
        p = (pos + 0.5) / length
        lengthoftext = len(text)
        distance_list = []
        vowel_list = []
        for i, s in enumerate(text):  # type: (int, object)
            if s in {'a', 'i', 'u', 'e', 'o'}:
                vowel_list.append(s)
                distance_list.append(abs(p - (i + 0.5) / lengthoftext))
        if len(distance_list) == 0:
            # 母音が無い
            return 'a'
        v = vowel_list[distance_list.index(min(distance_list))]
        # uはaに置き換える
        if v == 'u':
            v = 'a'
        return v


if __name__ == "__main__":
    i2k = ipa2Kana()
    ipa = "EY K AA T"
    print(ipa, " -> ", i2k.convert(ipa))
