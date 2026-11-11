const test=require('node:test');
const assert=require('node:assert/strict');
const {s2e,e2s}=require('../assets/js/enshu-converter-engine.js');
test('new context-based weather examples translate both ways',()=>{
 assert.equal(s2e('雨で道がぬかるんでいる。','futsu'),'雨で道がじゅるい。');
 assert.equal(e2s('雨で道がじゅるい。'),'雨で道がぬかるんでいる。');
 assert.equal(s2e('道がぬかるんでいて歩きにくい。','futsu'),'道がじゅるくて歩きにくい。');
 assert.equal(e2s('道がじゅるかった。'),'道がぬかるんでいた。');
});
test('lookup examples preserve the intended lexical meanings',()=>{
 assert.equal(s2e('急いで買ってくるよ。','futsu'),'ちゃっと買ってくるに。');
 assert.equal(e2s('ちゃっと'),'すぐに');
 assert.equal(e2s('ちゃっと買ってくるに。'),'すぐに買ってくるよ。');
 assert.equal(s2e('今日は疲れた。','futsu'),'今日はえらい。');
 assert.equal(s2e('前髪がうっとうしい。','futsu'),'前髪がやぶせったい。');
});
test('reverse conversion leaves ordinary words containing suffix text intact',()=>{
 for(const text of ['いたずら。','いたずらをしない。','だらしない服。','まだら。','だらだら歩く。','おしまい。','そうなんだ。','椅子をずらす。'])assert.equal(e2s(text),text,text);
});
test('suffix correction still handles actual dialect endings',()=>{
 assert.equal(e2s('明日は雨だら。'),'明日は雨だろう。');
 assert.equal(e2s('そうずらなあ。'),'そうだろうなあ。');
 assert.equal(e2s('一緒にしまい。'),'一緒にしよう。');
 assert.equal(e2s('行かなんだ。'),'行かなかった。');
 assert.equal(s2e('雨でしょう。','gachi'),'雨ずら。');
});
test('plain input, empty input and markup remain plain strings',()=>{
 assert.equal(s2e('','futsu'),'');assert.equal(e2s(''),'');
 assert.equal(s2e('<img src=x onerror=alert(1)>','futsu'),'<img src=x onerror=alert(1)>');
 assert.equal(s2e('ABC123','futsu'),'ABC123');
});
